import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.models.post import SocialPost
from app.models.approval import ApprovalRequest


class PostRepository:
    """
    Repository class encapsulating database operations for SocialPosts and ApprovalRequests.
    """
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_post_by_id(self, post_id: uuid.UUID) -> SocialPost | None:
        """
        Retrieves a social post by UUID with its approvals eagerly loaded.
        """
        stmt = (
            select(SocialPost)
            .options(joinedload(SocialPost.approval_requests))
            .filter(SocialPost.id == post_id)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create_post(self, post: SocialPost) -> SocialPost:
        """
        Persists a new social post.
        """
        self.db.add(post)
        await self.db.flush()
        return post

    async def update_post(self, post: SocialPost) -> SocialPost:
        """
        Updates an existing social post.
        """
        self.db.add(post)
        await self.db.flush()
        return post

    async def get_approval_by_id(
        self,
        approval_id: uuid.UUID
    ) -> ApprovalRequest | None:
        """
        Retrieves an approval request by UUID with the parent post eagerly loaded.
        """
        stmt = (
            select(ApprovalRequest)
            .options(joinedload(ApprovalRequest.post))
            .filter(ApprovalRequest.id == approval_id)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create_approval_request(
        self,
        approval: ApprovalRequest
    ) -> ApprovalRequest:
        """
        Persists a new approval request.
        """
        self.db.add(approval)
        await self.db.flush()
        return approval

    async def update_approval_request(
        self,
        approval: ApprovalRequest
    ) -> ApprovalRequest:
        """
        Updates an existing approval request.
        """
        self.db.add(approval)
        await self.db.flush()
        return approval

    async def get_pending_approvals(self) -> List[ApprovalRequest]:
        """
        Retrieves all pending approval requests.
        """
        stmt = (
            select(ApprovalRequest)
            .options(joinedload(ApprovalRequest.post))
            .filter(ApprovalRequest.status == "pending")
            .order_by(ApprovalRequest.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
