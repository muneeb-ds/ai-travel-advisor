"""
Pydantic schemas for knowledge base.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

# from app.models.knowledge_base import KnowledgeScope
# from app.schemas.destination import Destination


# Knowledge Base schemas
class KnowledgeBaseBase(BaseModel):
    """Base schema for knowledge base entry."""

    content: str = Field(..., min_length=1, description="Content of the knowledge entry")


class KnowledgeBaseItemCreate(BaseModel):
    """Schema for creating a new knowledge base entry."""

    title: str = Field(..., min_length=1, description="Name of the knowledge entry")
    scope: str = Field(..., min_length=1, description="Scope of the knowledge entry")
    destination_id: UUID = Field(..., description="Destination ID of the knowledge entry")


class KnowledgeBaseItemUpdate(BaseModel):
    """Schema for updating a knowledge base entry."""

    title: str | None = Field(None, min_length=1)
    # source_type: str | None = Field(None, min_length=1)
    # source_ref: str | None = Field(None, min_length=1)
    scope: str | None = Field(None, min_length=1, description="Scope of the knowledge entry")
    destination_id: UUID | None = Field(None, description="Destination ID of the knowledge entry")


class KnowledgeBaseResponse(BaseModel):
    """Schema for knowledge base response."""

    id: UUID
    title: str
    scope: str
    destination_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# class KnowledgeBaseWithDestination(KnowledgeBase):
#     """Schema for knowledge base with destination info."""
#     destination: Destination
