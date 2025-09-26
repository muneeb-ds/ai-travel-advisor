"""
User model for the Travel Advisor application.
"""

import enum
import uuid

from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserRole(enum.Enum):
    """User roles for RBAC."""

    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class User(Base):
    """Model for users with multi-tenant auth and RBAC."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Multi-tenancy
    org_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # RBAC
    role = Column(String(20), nullable=False, default=UserRole.MEMBER.value)
    is_active = Column(Boolean, default=True, nullable=False)

    __table_args__ = (CheckConstraint(role.in_(["ADMIN", "MEMBER"]), name="check_user_role"),)

    # Security features
    last_login_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=True, default=None, onupdate=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="users")
    destinations = relationship("Destination", back_populates="user", cascade="all, delete-orphan")
    knowledge_entries = relationship(
        "KnowledgeBase", back_populates="user", cascade="all, delete-orphan"
    )
    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
    agent_runs = relationship("AgentRun", back_populates="user", cascade="all, delete-orphan")
    itineraries = relationship("Itinerary", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role={self.role})>"
