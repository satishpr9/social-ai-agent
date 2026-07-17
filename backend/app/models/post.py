import uuid
from datetime import datetime
from typing import List
from sqlalchemy import String, DateTime, ForeignKey, Text, ARRAY, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


class SocialPost(Base):
    # Base class automatically maps to "social_posts"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    # Native PostgreSQL array of strings for target channels
    platforms: Mapped[List[str]] = mapped_column(
        ARRAY(String(50)),
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="draft",
        server_default="draft",
        index=True,
        nullable=False
    )
    scheduled_publish_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    actual_publish_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
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
    user: Mapped["User"] = relationship("User")
    
    approval_requests: Mapped[List["ApprovalRequest"]] = relationship(
        "ApprovalRequest",
        back_populates="post",
        cascade="all, delete-orphan"
    )
