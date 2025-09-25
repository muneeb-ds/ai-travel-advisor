"""
AgentRun model for audit trail and tool execution logs.
"""

import uuid
from enum import Enum as PyEnum

from sqlalchemy import Column, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class AgentRunStatus(PyEnum):
    """Status of agent execution."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentRun(Base):
    """Model for agent execution audit trail."""

    __tablename__ = "agent_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)

    # Multi-tenancy and user tracking
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)

    # Execution metadata
    trace_id = Column(String(255), nullable=False, index=True)
    status = Column(String(50), nullable=False, default=AgentRunStatus.RUNNING.value)

    # Agent state snapshots
    plan_snapshot = Column(JSONB, nullable=True)
    tool_log = Column(JSONB, nullable=True)
    final_result = Column(JSONB, nullable=True)

    # Cost tracking
    cost_usd = Column(Numeric(8, 2), nullable=True)

    # Error handling
    error_message = Column(Text, nullable=True)

    # Timestamps
    started_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    finished_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="agent_runs")
    user = relationship("User", back_populates="agent_runs")

    def __repr__(self):
        return f"<AgentRun(id={self.id}, trace_id='{self.trace_id}', status={self.status})>"
