# AI Chat schemas
from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Schema for AI chat request."""

    message: str = Field(..., min_length=1, description="User's question or message")
    destination_id: UUID | None = Field(None, description="Optional destination ID for context")


class ChatResponse(BaseModel):
    """Schema for AI chat response."""

    response: str = Field(..., description="AI's response to the user's message")
    sources: list[str] = Field(default=[], description="Sources used for the response")
    weather_data: dict | None = Field(None, description="Weather data if requested")
