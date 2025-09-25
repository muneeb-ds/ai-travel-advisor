"""
Organization model for multi-tenant Travel Advisor application.
"""

import uuid

from sqlalchemy import Boolean, Column, String, func
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Organization(Base):
    """Model for organizations (multi-tenancy)."""

    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=True, default=None, onupdate=func.now())

    # Relationships
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    destinations = relationship("Destination", back_populates="organization")
    knowledge_entries = relationship("KnowledgeBase", back_populates="organization")
    agent_runs = relationship("AgentRun", back_populates="organization")
    itineraries = relationship("Itinerary", back_populates="organization")

    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}')>"
