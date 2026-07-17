from datetime import datetime
import uuid
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

# Dynamic regex pattern for email checking
EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


class ProfileBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=150)
    avatar_url: str | None = Field(default=None, max_length=512)
    phone_number: str | None = Field(default=None, max_length=20)
    company_name: str | None = Field(default=None, max_length=100)


class ProfileResponse(ProfileBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    # Pydantic v2 configuration enabling ORM serialization
    model_config = ConfigDict(from_attributes=True)


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=150)
    avatar_url: str | None = Field(default=None, max_length=512)
    phone_number: str | None = Field(default=None, max_length=20)
    company_name: str | None = Field(default=None, max_length=100)


class UserBase(BaseModel):
    email: str = Field(..., pattern=EMAIL_REGEX)
    role: Literal["admin", "editor", "viewer"] = "viewer"
    is_active: bool = True
    is_verified: bool = False


class UserCreate(BaseModel):
    email: str = Field(..., pattern=EMAIL_REGEX)
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=150)


class UserUpdate(BaseModel):
    email: str | None = Field(default=None, pattern=EMAIL_REGEX)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    role: Literal["admin", "editor", "viewer"] | None = None
    is_active: bool | None = None
    is_verified: bool | None = None


class UserResponse(UserBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    profile: ProfileResponse | None = None

    model_config = ConfigDict(from_attributes=True)
