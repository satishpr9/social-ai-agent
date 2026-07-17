import uuid
from typing import List
from pydantic import BaseModel, Field


class ProposalItem(BaseModel):
    name: str = Field(..., max_length=255)
    type: str = Field(default="One-Time", max_length=50) # e.g. "One-Time", "Recurring"
    price: str = Field(..., max_length=50) # e.g. "$499"


class ProposalCreateRequest(BaseModel):
    """
    Validation schema to trigger a new sales proposal compilation.
    """
    lead_id: uuid.UUID
    items: List[ProposalItem]
    total_price: str = Field(..., max_length=50)


class ProposalResponse(BaseModel):
    """
    Returns the secure object-store pre-signed download link.
    """
    download_url: str
