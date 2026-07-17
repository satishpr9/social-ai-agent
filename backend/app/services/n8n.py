import asyncio
import logging
import uuid
from datetime import datetime, timezone
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.db.session import async_session_factory
from app.repositories.post import PostRepository
from app.models.post import SocialPost
from app.schemas.n8n import N8NCallbackPayload

logger = logging.getLogger("app.services.n8n")


class N8NService:
    """
    Service class responsible for publishing dispatches, callbacks,
    and scheduled campaign background polling.
    """
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = PostRepository(db)

    async def dispatch_post_to_n8n(self, post: SocialPost) -> bool:
        """
        Sends the post details to the n8n webhook publishing workflow.
        """
        # If webhook URL is mock or empty, log and bypass actual network calls
        if not settings.N8N_WEBHOOK_URL or "localhost" in settings.N8N_WEBHOOK_URL and settings.ENVIRONMENT == "testing":
            logger.info(f"Bypassing n8n network dispatch in test mode for post: {post.id}")
            return True

        payload = {
            "post_id": str(post.id),
            "title": post.title,
            "content": post.content,
            "platforms": post.platforms
        }
        
        headers = {
            "X-App-Secret": settings.N8N_SHARED_SECRET,
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    settings.N8N_WEBHOOK_URL,
                    json=payload,
                    headers=headers
                )
                if response.status_code in [200, 201, 202]:
                    logger.info(f"Successfully dispatched post {post.id} to n8n.")
                    return True
                else:
                    logger.error(
                        f"Failed to dispatch post {post.id} to n8n. "
                        f"Status: {response.status_code}, Body: {response.text}"
                    )
                    return False
        except Exception as e:
            logger.error(f"Error connecting to n8n webhook: {e}")
            return False

    async def process_n8n_callback(self, payload: N8NCallbackPayload) -> SocialPost:
        """
        Processes callbacks from n8n to transition post publication status.
        """
        post = await self.repo.get_post_by_id(payload.post_id)
        if not post:
            raise ValueError("Social post associated with callback not found.")

        if payload.status == "success":
            post.status = "published"
            post.actual_publish_time = datetime.now(timezone.utc)
            logger.info(f"Post {post.id} successfully marked as published.")
        else:
            post.status = "failed"
            logger.warning(
                f"Post {post.id} marked as failed. "
                f"Reason: {payload.error_message}"
            )

        await self.repo.update_post(post)
        await self.db.commit()
        return post


# ----------------------------------------------------
# Background Task Loop Scheduler
# ----------------------------------------------------

async def publish_scheduled_posts_loop() -> None:
    """
    Infinite background loop that polls PostgreSQL every 60 seconds
    for approved posts whose scheduled publish time has arrived,
    and dispatches them to n8n.
    """
    logger.info("Starting background scheduled post publication scheduler loop...")
    while True:
        try:
            now = datetime.now(timezone.utc)
            
            # Open a clean, isolated session for background thread safety
            async with async_session_factory() as session:
                stmt = (
                    select(SocialPost)
                    .filter(SocialPost.status == "approved")
                    .filter(SocialPost.scheduled_publish_time <= now)
                )
                result = await session.execute(stmt)
                due_posts = result.scalars().all()

                if due_posts:
                    logger.info(f"Found {len(due_posts)} scheduled posts due for publication.")
                    n8n_service = N8NService(session)
                    
                    for post in due_posts:
                        # 1. Update status to 'publishing' to prevent double-polling
                        post.status = "publishing"
                        session.add(post)
                        await session.flush()
                        
                        # 2. Dispatch to n8n
                        success = await n8n_service.dispatch_post_to_n8n(post)
                        if not success:
                            # Revert status to approved so scheduler tries again later, or fail
                            post.status = "approved"
                            session.add(post)
                            
                    await session.commit()
                    
        except asyncio.CancelledError:
            logger.info("Background publication loop cancelled. Shutting down...")
            break
        except Exception as e:
            logger.error(f"Error in background publication loop: {e}", exc_info=True)
            
        # Poll every 60 seconds
        await asyncio.sleep(60)
