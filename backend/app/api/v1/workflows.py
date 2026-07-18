import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.workflow import AgentGenerateRequest, AgentGenerateResponse
from app.services.workflow import WorkflowService

logger = logging.getLogger("app.api.v1.workflows")

router = APIRouter()


@router.post(
    "/generate",
    response_model=AgentGenerateResponse,
    status_code=status.HTTP_201_CREATED
)
async def generate_workflow_content(
    request: AgentGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AgentGenerateResponse:
    """
    Triggers the autonomous agent pipeline (Research -> SEO Blog -> Social Copy),
    compiles the generated content, and saves a draft post linked to the authenticated user.
    """
    logger.info(f"User {current_user.email} triggered content generation workflow.")
    
    workflow_service = WorkflowService(db)
    try:
        draft_post = await workflow_service.execute_agent_pipeline(
            topic=request.topic,
            platforms=request.platforms,
            user_id=current_user.id
        )
        
        return AgentGenerateResponse(
            post_id=draft_post.id,
            title=draft_post.title,
            status=draft_post.status,
            message="Content successfully generated and saved as a draft."
        )
    except Exception as e:
        logger.error(f"Failed to execute agent generation pipeline: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content generation pipeline execution failed: {str(e)}"
        )
