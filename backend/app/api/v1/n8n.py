import logging
import secrets
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.schemas.n8n import N8NCallbackPayload, N8NCallbackResponse
from app.services.n8n import N8NService

logger = logging.getLogger("app.api.v1.n8n")

router = APIRouter()


async def validate_n8n_secret(
    x_app_secret: str = Header(..., alias="X-App-Secret")
) -> None:
    """
    Security dependency validating that incoming requests from n8n
    present the correct shared secret. Protects against timing attacks.
    """
    # Prevent weak validation if the shared secret is not set in environment settings
    if not settings.N8N_SHARED_SECRET:
        logger.critical("N8N_SHARED_SECRET is not configured in the application settings!")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication system is misconfigured."
        )

    # Use secrets.compare_digest to prevent timing attack side-channels
    if not secrets.compare_digest(x_app_secret, settings.N8N_SHARED_SECRET):
        logger.warning("Invalid shared secret presented on n8n callback webhook.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid shared webhook secret credentials."
        )


@router.post(
    "/callback",
    status_code=status.HTTP_200_OK,
    response_model=N8NCallbackResponse,
    dependencies=[Depends(validate_n8n_secret)]
)
async def n8n_callback(
    payload: N8NCallbackPayload,
    db: AsyncSession = Depends(get_db)
) -> N8NCallbackResponse:
    """
    Asynchronous callback webhook invoked by n8n to notify our backend
    of social publishing outcomes.
    """
    logger.info(
        f"Received publication callback from n8n for post: {payload.post_id} "
        f"with status: {payload.status}"
    )

    n8n_service = N8NService(db)
    try:
        await n8n_service.process_n8n_callback(payload)
        logger.info(f"Successfully processed n8n callback for post: {payload.post_id}")
        
        return N8NCallbackResponse(
            success=True,
            message="Callback processed successfully",
            data={
                "post_id": str(payload.post_id),
                "status": "processed"
            }
        )
    except ValueError as e:
        logger.warning(
            f"Validation failure in n8n callback for post {payload.post_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            f"Unexpected exception during processing n8n callback for post {payload.post_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error processing callback."
        )

