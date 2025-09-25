"""
Knowledge base model for the Travel Advisor application.
"""

import enum
import uuid

from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class KnowledgeScope(enum.Enum):
    """Visibility scope for knowledge items."""

    ORG_PUBLIC = "org_public"
    PRIVATE = "private"


class KnowledgeBase(Base):
    """Model for knowledge base entries about destinations."""

    __tablename__ = "knowledge_base"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)

    # Content
    title = Column(String(500), nullable=False)
    # content = Column(Text, nullable=False)
    # source_type = Column(String(50), nullable=False)  # pdf, markdown, manual, url
    # source_ref = Column(Text, nullable=True)  # file path, URL, etc.

    # Multi-tenancy and relationships
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    destination_id = Column(
        UUID(as_uuid=True), ForeignKey("destinations.id", ondelete="CASCADE"), nullable=True
    )  # Optional association

    # Visibility scope
    scope = Column(String(20), nullable=False, default=KnowledgeScope.ORG_PUBLIC.value)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_processed = Column(Boolean, default=False, nullable=False)  # For embedding generation

    __table_args__ = (
        CheckConstraint(scope.in_(["org_public", "private"]), name="check_knowledge_scope"),
    )

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=True, default=None, onupdate=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="knowledge_entries")
    user = relationship("User", back_populates="knowledge_entries")
    destination = relationship("Destination", back_populates="knowledge_entries")
    embeddings = relationship(
        "Embedding", back_populates="knowledge_item", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<KnowledgeBase(id={self.id}, title='{self.title}', scope={self.scope})>"
