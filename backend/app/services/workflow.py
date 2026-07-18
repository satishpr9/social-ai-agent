import logging
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import SocialPost
from app.repositories.post import PostRepository
from app.workflows.research import research_agent
from app.workflows.seo import seo_agent
from app.workflows.social import social_agent

logger = logging.getLogger("app.services.workflow")


class WorkflowService:
    """
    Business service that chains LangGraph agents (Research, SEO, Social)
    together and saves the compiled draft social post in the database.
    """
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = PostRepository(db)

    async def execute_agent_pipeline(
        self,
        topic: str,
        platforms: list[str],
        user_id: uuid.UUID | None = None
    ) -> SocialPost:
        """
        Executes the content generation pipeline end-to-end.
        """
        logger.info(f"Initiating agent pipeline execution for topic: '{topic}'")

        # 1. Run Research Agent
        logger.info("Executing Research Agent...")
        research_state = await research_agent.ainvoke({"query": topic})
        research_report = research_state.get("summary", "")
        if not research_report:
            logger.warning("Research Agent returned an empty report.")

        # 2. Run SEO Blog Agent
        logger.info("Executing SEO Blog Agent...")
        seo_state = await seo_agent.ainvoke({"research_report": research_report})
        title = seo_state.get("generated_title", f"AI Generated Post: {topic}")
        slug = seo_state.get("generated_slug", "")
        blog_content = seo_state.get("generated_blog_content", "")
        seo_keywords = seo_state.get("seo_keywords", [])
        meta_description = seo_state.get("meta_description", "")
        image_prompt = seo_state.get("image_prompt", "")

        # 3. Run Social Media Caption Agent
        logger.info("Executing Social Caption Agent...")
        social_state = await social_agent.ainvoke({
            "blog_title": title,
            "blog_content": blog_content
        })
        linkedin_post = social_state.get("linkedin_post", "")
        twitter_thread = social_state.get("twitter_thread", [])
        facebook_post = social_state.get("facebook_post", "")
        instagram_caption = social_state.get("instagram_caption", "")

        # 4. Compile into unified markdown document
        compiled_markdown = self._compile_markdown_report(
            blog_content=blog_content,
            slug=slug,
            keywords=seo_keywords,
            meta_description=meta_description,
            image_prompt=image_prompt,
            linkedin_post=linkedin_post,
            twitter_thread=twitter_thread,
            facebook_post=facebook_post,
            instagram_caption=instagram_caption
        )

        # 5. Persist to DB as a draft
        logger.info("Persisting drafted social post and cataloging workflow...")
        db_post = SocialPost(
            user_id=user_id,
            title=title,
            content=compiled_markdown,
            platforms=platforms,
            status="draft"
        )
        
        await self.repo.create_post(db_post)
        await self.db.commit()
        
        logger.info(f"Workflow pipeline complete. SocialPost created with ID: {db_post.id}")
        return db_post

    def _compile_markdown_report(
        self,
        blog_content: str,
        slug: str,
        keywords: list[str],
        meta_description: str,
        image_prompt: str,
        linkedin_post: str,
        twitter_thread: list[str],
        facebook_post: str,
        instagram_caption: str
    ) -> str:
        """
        Formats all generated outputs into a single structured markdown document.
        """
        # Format twitter thread list cleanly
        tweets_str = "\n\n".join([f"**Tweet {i+1}:**\n{tweet}" for i, tweet in enumerate(twitter_thread)])
        
        markdown = f"""{blog_content}

---

## 🔍 SEO & Metadata Insights
* **Target Slug**: `{slug}`
* **Keywords**: {", ".join([f"`{kw}`" for kw in keywords])}
* **Meta Description**: *{meta_description}*
* **Banner Image Prompt**: 
  > {image_prompt}

---

## 📱 Social Media Copy Drafts

### 💼 LinkedIn Draft
{linkedin_post}

---

### 🐦 Twitter/X Thread Draft
{tweets_str}

---

### 👥 Facebook Draft
{facebook_post}

---

### 📸 Instagram Draft
{instagram_caption}
"""
        return markdown.strip()
