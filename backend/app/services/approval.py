import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.post import PostRepository
from app.models.post import SocialPost
from app.models.approval import ApprovalRequest
from app.schemas.post import SocialPostCreate


class ApprovalService:
    """
    Business service layer orchestrating the state machine transitions for SocialPosts and Approvals.
    """
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = PostRepository(db)

    async def submit_post_for_approval(
        self,
        post_in: SocialPostCreate,
        user_id: uuid.UUID
    ) -> ApprovalRequest:
        """
        Creates a post in 'pending_approval' state and registers an approval request.
        """
        # 1. Create the social post record
        db_post = SocialPost(
            user_id=user_id,
            title=post_in.title,
            content=post_in.content,
            platforms=post_in.platforms,
            status="pending_approval",
            scheduled_publish_time=post_in.scheduled_publish_time
        )
        await self.repo.create_post(db_post)

        # 2. Create the approval request record linked to this post
        db_approval = ApprovalRequest(
            post_id=db_post.id,
            requested_by=user_id,
            status="pending"
        )
        await self.repo.create_approval_request(db_approval)

        # Commit transaction atomically
        await self.db.commit()
        return db_approval

    async def approve_request(
        self,
        approval_id: uuid.UUID,
        reviewer_id: uuid.UUID,
        comments: str | None = None
    ) -> ApprovalRequest:
        """
        Approves an approval request and transitions the associated post to 'approved'.
        """
        approval = await self.repo.get_approval_by_id(approval_id)
        if not approval:
            raise ValueError("Approval request not found.")
            
        if approval.status != "pending":
            raise ValueError(f"Cannot approve request. Current status is '{approval.status}'.")

        # Update approval request details
        approval.status = "approved"
        approval.approved_by = reviewer_id
        approval.comments = comments

        # Transition post status to approved (ready to publish)
        approval.post.status = "approved"

        # Save both changes atomically
        await self.repo.update_approval_request(approval)
        await self.db.commit()
        return approval

    async def reject_request(
        self,
        approval_id: uuid.UUID,
        reviewer_id: uuid.UUID,
        comments: str | None = None
    ) -> ApprovalRequest:
        """
        Rejects an approval request and transitions the associated post back to 'draft'.
        """
        approval = await self.repo.get_approval_by_id(approval_id)
        if not approval:
            raise ValueError("Approval request not found.")
            
        if approval.status != "pending":
            raise ValueError(f"Cannot reject request. Current status is '{approval.status}'.")

        # Rejection requires comments
        if not comments or not comments.strip():
            raise ValueError("Reviewer feedback/comments are required for rejecting posts.")

        # Update approval request details
        approval.status = "rejected"
        approval.approved_by = reviewer_id
        approval.comments = comments

        # Transition post status back to draft for adjustments
        approval.post.status = "draft"

        # Save changes atomically
        await self.repo.update_approval_request(approval)
        await self.db.commit()
        return approval

    async def get_pending_requests(self) -> List[ApprovalRequest]:
        """
        Retrieves all pending approval requests.
        """
        return await self.repo.get_pending_approvals()
