import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LeadBase(BaseModel):
    email: str = Field(..., max_length=255) # We use str to avoid EmailStr external dependency crashes
    full_name: str | None = Field(default=None, max_length=255)
    company: str | None = Field(default=None, max_length=255)


class LeadCreate(LeadBase):
    """
    Schema for capturing a lead, including attribution properties
    and UTM parameters.
    """
    source_platform: str | None = Field(default=None, max_length=50)
    source_post_id: uuid.UUID | None = None
    utm_source: str | None = Field(default=None, max_length=100)
    utm_medium: str | None = Field(default=None, max_length=100)
    utm_campaign: str | None = Field(default=None, max_length=100)


class LeadUpdate(BaseModel):
    """
    Schema for updating a lead's metadata or moving them through the pipeline.
    """
    full_name: str | None = Field(default=None, max_length=255)
    company: str | None = Field(default=None, max_length=255)
    status: str | None = Field(default=None, max_length=50)


class LeadResponse(LeadBase):
    id: uuid.UUID
    status: str
    source_platform: str | None
    source_post_id: uuid.UUID | None
    utm_source: str | None
    utm_medium: str | None
    utm_campaign: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
