import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


class ApprovalRequest(Base):
    # Base class automatically maps to "approval_requests"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )
    post_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("social_posts.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    requested_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        server_default="pending",
        index=True,
        nullable=False
    )
    comments: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    post: Mapped["SocialPost"] = relationship(
        "SocialPost",
        back_populates="approval_requests"
    )
    
    # Dual relationship mapping targeting the User class, resolved via foreign_keys
    requester: Mapped["User"] = relationship(
        "User",
        foreign_keys=[requested_by]
    )
    approver: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[approved_by]
    )
ActiveUser = "User" # Helper reference mapping type hint compatibility
from app.models.user import User # Import user for type checking resolution
