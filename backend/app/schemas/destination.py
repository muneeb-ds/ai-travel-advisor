"""
Pydantic schemas for Destination.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.knowledge_base import KnowledgeBaseResponse


# Destination schemas
class DestinationBase(BaseModel):
    """Base schema for destination."""

    name: str = Field(..., min_length=1, max_length=255, description="Name of the destination")


class DestinationCreate(DestinationBase):
    """Schema for creating a new destination."""

    pass


class DestinationUpdate(BaseModel):
    """Schema for updating a destination."""

    name: str | None = Field(None, min_length=1, max_length=255)


class Destination(DestinationBase):
    """Schema for destination response."""

    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class DestinationWithKnowledge(Destination):
    """Schema for destination with knowledge entries."""

    knowledge_entries: list["KnowledgeBaseResponse"] = []
