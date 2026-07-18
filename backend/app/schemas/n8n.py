import uuid
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field


class N8NCallbackPayload(BaseModel):
    """
    Schema for payloads sent by n8n to notify FastAPI of publication outcomes.
    """
    post_id: uuid.UUID
    status: Literal["success", "failed"]
    error_message: str | None = Field(default=None, max_length=2000)


class N8NCallbackResponse(BaseModel):
    """Response model for n8n callback endpoints."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Callback processed successfully",
                "data": {
                    "execution_id": "exec_123456",
                    "status": "completed",
                },
            }
        },
    )

    success: bool = Field(
        ...,
        description="Indicates whether the callback was processed successfully.",
    )
    message: str = Field(
        ...,
        description="Human-readable response message.",
    )
    data: dict[str, Any] | None = Field(
        default=None,
        description="Optional payload containing additional callback information.",
    )

