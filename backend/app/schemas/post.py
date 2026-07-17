import uuid
from datetime import datetime
from typing import List, Literal
from pydantic import BaseModel, ConfigDict, Field


class SocialPostBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    platforms: List[str] = Field(..., min_items=1)
    scheduled_publish_time: datetime | None = None


class SocialPostCreate(SocialPostBase):
    pass


class SocialPostResponse(SocialPostBase):
    id: uuid.UUID
    user_id: uuid.UUID | None
    status: str
    actual_publish_time: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApprovalActionRequest(BaseModel):
    """
    Schema representing reviewer feedback when approving or rejecting a post.
    """
    comments: str | None = Field(default=None, max_length=1000)


class ApprovalRequestResponse(BaseModel):
    id: uuid.UUID
    post_id: uuid.UUID
    requested_by: uuid.UUID
    approved_by: uuid.UUID | None
    status: str
    comments: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
