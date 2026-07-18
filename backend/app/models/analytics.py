import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Integer, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


class AnalyticsMetric(Base):
    # Base class automatically maps to "analytics_metrics"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )
    post_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("social_posts.id", ondelete="CASCADE"),
        index=True,
        nullable=True
    )
    metric_type: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False # e.g. "views", "likes", "clicks"
    )
    metric_value: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False
    )
    platform: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False # e.g. "linkedin", "twitter", "facebook", "instagram"
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
        index=True,
        nullable=False
    )

    # Relationships
    post: Mapped["SocialPost | None"] = relationship("SocialPost")


from app.models.post import SocialPost # Import for relationship resolution type checking
