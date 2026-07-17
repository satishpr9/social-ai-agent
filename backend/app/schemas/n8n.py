import uuid
from typing import Literal
from pydantic import BaseModel, Field


class N8NCallbackPayload(BaseModel):
    """
    Schema for payloads sent by n8n to notify FastAPI of publication outcomes.
    """
    post_id: uuid.UUID
    status: Literal["success", "failed"]
    error_message: str | None = Field(default=None, max_length=2000)
