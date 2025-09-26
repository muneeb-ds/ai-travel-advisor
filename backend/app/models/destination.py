"""
Destination model for the Travel Advisor application.
"""

import uuid

from sqlalchemy import Boolean, Column, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Destination(Base):
    """Model for travel destinations."""

    __tablename__ = "destinations"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Multi-tenancy
    org_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Soft delete
    is_active = Column(Boolean, default=True, nullable=False)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=True, default=None, onupdate=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="destinations")
    user = relationship("User", back_populates="destinations")
    knowledge_entries = relationship(
        "KnowledgeBase", back_populates="destination", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Destination(id={self.id}, name='{self.name}')>"
