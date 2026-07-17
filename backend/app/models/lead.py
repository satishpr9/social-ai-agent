import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


class Lead(Base):
    # Base class automatically maps to "leads"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )
    email: Mapped[str] = mapped_column(
        String(255),
        index=True,
        unique=True,
        nullable=False
    )
    full_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )
    company: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="new",
        server_default="new",
        index=True,
        nullable=False # e.g. "new", "contacted", "converted", "lost"
    )
    source_platform: Mapped[str | None] = mapped_column(
        String(50),
        index=True,
        nullable=True # e.g. "linkedin", "twitter", "facebook"
    )
    source_post_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("social_posts.id", ondelete="SET NULL"),
        index=True,
        nullable=True
    )
    utm_source: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )
    utm_medium: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )
    utm_campaign: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    post: Mapped["SocialPost | None"] = relationship("SocialPost")


from app.models.post import SocialPost # Import User/Post types for relations mapping
ActiveUser = "User"
