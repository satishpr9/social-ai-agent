from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.schemas.n8n import N8NCallbackPayload
from app.services.n8n import N8NService

router = APIRouter()


async def validate_n8n_secret(
    x_app_secret: str = Header(..., alias="X-App-Secret")
) -> None:
    """
    Security dependency validating that incoming requests from n8n
    present the correct shared secret.
    """
    if x_app_secret != settings.N8N_SHARED_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid shared webhook secret credentials."
        )


@router.post(
    "/callback",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(validate_n8n_secret)]
)
async def n8n_callback(
    payload: N8NCallbackPayload,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Asynchronous callback webhook invoked by n8n to notify our backend
    of social publishing outcomes.
    """
    n8n_service = N8NService(db)
    try:
        await n8n_service.process_n8n_callback(payload)
        return {"status": "processed", "post_id": str(payload.post_id)}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
