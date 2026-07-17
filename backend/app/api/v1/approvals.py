import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.api.deps import get_current_user, RoleChecker
from app.models.user import User
from app.schemas.post import (
    SocialPostCreate,
    ApprovalActionRequest,
    ApprovalRequestResponse
)
from app.services.approval import ApprovalService
from app.services.email import EmailService

router = APIRouter()

# Instantiate RBAC checkers
require_editor_or_admin = Depends(RoleChecker(["admin", "editor"]))


@router.post(
    "/submit",
    response_model=ApprovalRequestResponse,
    status_code=status.HTTP_201_CREATED
)
async def submit_post(
    post_in: SocialPostCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ApprovalRequestResponse:
    """
    Submit a newly generated blog post for editor/admin review.
    Creates both the post and the linked approval request.
    Dispatches a review notification email in the background.
    """
    approval_service = ApprovalService(db)
    approval = await approval_service.submit_post_for_approval(
        post_in=post_in,
        user_id=current_user.id
    )

    # Dispatch email notification in the background
    email_service = EmailService()
    background_tasks.add_task(
        email_service.send_approval_email,
        to_email=settings.EMAILS_FROM_EMAIL,
        approval_id=approval.id,
        post_title=post_in.title,
        submitter_name=current_user.email,
        platforms=post_in.platforms
    )

    return approval


@router.get(
    "/pending",
    response_model=List[ApprovalRequestResponse],
    dependencies=[require_editor_or_admin]
)
async def list_pending_approvals(
    db: AsyncSession = Depends(get_db)
) -> List[ApprovalRequestResponse]:
    """
    List all pending content approval requests. Restricted to Admin/Editor.
    """
    approval_service = ApprovalService(db)
    pending = await approval_service.get_pending_requests()
    return pending


@router.post(
    "/{approval_id}/approve",
    response_model=ApprovalRequestResponse
)
async def approve_post(
    approval_id: uuid.UUID,
    action_in: ApprovalActionRequest,
    current_user: User = Depends(RoleChecker(["admin", "editor"])),
    db: AsyncSession = Depends(get_db)
) -> ApprovalRequestResponse:
    """
    Approve content for publishing. Restricted to Admin/Editor.
    """
    approval_service = ApprovalService(db)
    try:
        updated_request = await approval_service.approve_request(
            approval_id=approval_id,
            reviewer_id=current_user.id,
            comments=action_in.comments
        )
        return updated_request
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/{approval_id}/reject",
    response_model=ApprovalRequestResponse
)
async def reject_post(
    approval_id: uuid.UUID,
    action_in: ApprovalActionRequest,
    current_user: User = Depends(RoleChecker(["admin", "editor"])),
    db: AsyncSession = Depends(get_db)
) -> ApprovalRequestResponse:
    """
    Reject content, reverting it to draft state. Requires feedback comments. Restricted to Admin/Editor.
    """
    approval_service = ApprovalService(db)
    try:
        updated_request = await approval_service.reject_request(
            approval_id=approval_id,
            reviewer_id=current_user.id,
            comments=action_in.comments
        )
        return updated_request
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
