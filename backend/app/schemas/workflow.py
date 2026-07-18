import uuid
from pydantic import BaseModel, Field


class AgentGenerateRequest(BaseModel):
    """
    Input schema for autonomous agent content generation.
    """
    topic: str = Field(
        ...,
        min_length=3,
        max_length=255,
        description="The topic to research and compile into content."
    )
    platforms: list[str] = Field(
        default=["linkedin", "twitter"],
        description="Social media platforms to generate copy for."
    )


class AgentGenerateResponse(BaseModel):
    """
    Output schema returned after successfully compiling agent outputs.
    """
    post_id: uuid.UUID = Field(
        ...,
        description="The database ID of the created SocialPost record."
    )
    title: str = Field(
        ...,
        description="The generated blog title."
    )
    status: str = Field(
        ...,
        description="Current status of the created post (e.g. 'draft')."
    )
    message: str = Field(
        ...,
        description="Status message indicating outcome."
    )
