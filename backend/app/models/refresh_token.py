"""
RefreshToken model for JWT token management with rotation.
"""

import uuid

from sqlalchemy import Boolean, Column, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class RefreshToken(Base):
    """Model for refresh tokens with rotation support."""

    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)

    # JWT claims
    jti = Column(String(255), unique=True, nullable=False, index=True)  # JWT ID
    token_hash = Column(String(255), nullable=False)  # Hashed token for server-side storage

    # User relationship
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Token metadata
    is_revoked = Column(Boolean, default=False, nullable=False)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    used_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="refresh_tokens")

    def __repr__(self):
        return f"<RefreshToken(id={self.id}, jti='{self.jti}', user_id={self.user_id})>"
