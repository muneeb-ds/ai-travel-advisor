"""
Itinerary model for persisting travel plans.
"""

import uuid

from sqlalchemy import Boolean, Column, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Itinerary(Base):
    """Model for travel itineraries."""

    __tablename__ = "itineraries"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)

    # Multi-tenancy and user tracking
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Itinerary metadata
    title = Column(String(500), nullable=False)
    destination = Column(String(255), nullable=False)

    # Trip details
    start_date = Column(TIMESTAMP(timezone=True), nullable=False)
    end_date = Column(TIMESTAMP(timezone=True), nullable=False)
    budget_usd = Column(Numeric(10, 2), nullable=True)
    total_cost_usd = Column(Numeric(10, 2), nullable=True)

    # Structured itinerary data
    itinerary_data = Column(JSONB, nullable=False)  # Days, items, etc.
    constraints = Column(JSONB, nullable=True)  # Original constraints
    preferences = Column(JSONB, nullable=True)  # User preferences

    # Citations and metadata
    citations = Column(JSONB, nullable=True)
    tools_used = Column(JSONB, nullable=True)
    decisions = Column(JSONB, nullable=True)

    # Agent execution reference
    agent_run_id = Column(UUID(as_uuid=True), ForeignKey("agent_runs.id"), nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Narrative content
    description = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=True, default=None, onupdate=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="itineraries")
    user = relationship("User", back_populates="itineraries")
    agent_run = relationship("AgentRun")

    def __repr__(self):
        return f"<Itinerary(id={self.id}, title='{self.title}', destination='{self.destination}')>"
