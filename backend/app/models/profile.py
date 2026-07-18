import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


class Profile(Base):
    # Base class automatically pluralizes the table name to "profiles"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True, # Enforces one-to-one relationship
        index=True,
        nullable=False
    )
    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )
    avatar_url: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True
    )
    phone_number: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )
    company_name: Mapped[str | None] = mapped_column(
        String(100),
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
    # Back-populates user model
    user: Mapped["User"] = relationship(
        "User",
        back_populates="profile"
    )
