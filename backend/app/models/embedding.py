"""
Embedding model with pgvector support for RAG knowledge base.
"""

import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Embedding(Base):
    """Model for text embeddings with pgvector."""

    __tablename__ = "embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)

    # Reference to knowledge item
    knowledge_item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_base.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Chunk information
    chunk_idx = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)

    # Vector embedding (1536 dimensions for OpenAI text-embedding-ada-002)
    embedding = Column(Vector(1536), nullable=False)

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())

    # Relationships
    knowledge_item = relationship("KnowledgeBase", back_populates="embeddings")

    def __repr__(self):
        return f"<Embedding(id={self.id}, knowledge_item_id={self.knowledge_item_id}, chunk_idx={self.chunk_idx})>"
