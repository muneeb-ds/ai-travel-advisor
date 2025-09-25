"""
Pydantic schemas for the LangGraph agent state and related structures.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel


class ConstraintType(str, Enum):
    """Types of constraints for travel planning."""

    BUDGET = "budget"
    DATES = "dates"
    PREFERENCES = "preferences"
    REQUIREMENTS = "requirements"


class ViolationType(str, Enum):
    """Types of constraint violations."""

    BUDGET_EXCEEDED = "budget_exceeded"
    INFEASIBLE_SCHEDULE = "infeasible_schedule"
    WEATHER_CONFLICT = "weather_conflict"
    PREFERENCE_MISMATCH = "preference_mismatch"


class ToolCallStatus(str, Enum):
    """Status of tool execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ProgressEvent(BaseModel):
    """Progress event for streaming."""

    trace_id: str
    node: str
    status: str
    timestamp: datetime
    message: str | None = None
    args_digest: str | None = None
    duration_ms: int | None = None


class Constraint(BaseModel):
    """Individual constraint."""

    type: ConstraintType
    key: str
    value: Any
    required: bool = True
    description: str | None = None


class Violation(BaseModel):
    """Constraint violation."""

    type: ViolationType
    constraint_key: str
    expected: Any
    actual: Any
    severity: str = "error"  # error, warning
    message: str


class ToolCall(BaseModel):
    """Tool execution record."""

    id: str
    name: str
    args: dict[str, Any]
    status: ToolCallStatus
    result: dict[str, Any] | None = None
    error: str | None = None
    duration_ms: int | None = None
    cache_hit: bool = False
    retries: int = 0


class PlanStep(BaseModel):
    """Individual step in the travel plan."""

    id: str
    name: str
    tool_calls: list[str]  # Tool call IDs
    dependencies: list[str] = []  # Step IDs this depends on
    parallel_group: str | None = None
    estimated_cost_usd: float | None = None
    estimated_duration_minutes: int | None = None


class Citation(BaseModel):
    """Citation for information sources."""

    title: str
    source: str  # url, manual, file, tool
    ref: str  # knowledge_id or tool_name#id
    chunk_idx: int | None = None


class ItineraryItem(BaseModel):
    """Individual item in the itinerary."""

    start: str  # ISO time
    end: str  # ISO time
    title: str
    location: str
    notes: str | None = None
    cost_usd: float | None = None
    booking_ref: str | None = None


class ItineraryDay(BaseModel):
    """Single day in the itinerary."""

    date: str  # ISO date
    items: list[ItineraryItem]
    daily_cost_usd: float | None = None


class ItineraryResult(BaseModel):
    """Final itinerary structure."""

    days: list[ItineraryDay]
    total_cost_usd: float
    currency: str = "USD"


class Decision(BaseModel):
    """Agent decision record."""

    step: str
    choice: str
    alternatives: list[str] = []
    reason: str


class BudgetCounter(BaseModel):
    """Budget tracking."""

    flights: float = 0.0
    lodging: float = 0.0
    activities: float = 0.0
    transportation: float = 0.0
    meals: float = 0.0
    total: float = 0.0
    currency: str = "USD"


class AgentState(BaseModel):
    """Typed state for the LangGraph agent."""

    # Input and context
    messages: list[dict[str, Any]] = []
    trace_id: str
    user_id: str
    org_id: str

    # Constraints and preferences
    constraints: list[Constraint] = []
    raw_query: str | None = None

    # Planning state
    plan: list[PlanStep] = []
    current_step: str | None = None
    working_set: dict[str, Any] = {}  # Intermediate results

    # Tool execution
    tool_calls: list[ToolCall] = []

    # Verification and repair
    violations: list[Violation] = []
    repair_attempts: int = 0

    # Results
    citations: list[Citation] = []
    decisions: list[Decision] = []
    budget_counters: BudgetCounter = BudgetCounter()
    final_itinerary: ItineraryResult | None = None

    # Control flow
    done: bool = False
    error: str | None = None

    # Checkpoints
    last_checkpoint: str | None = None
    checkpoint_data: dict[str, Any] = {}


class FinalResult(BaseModel):
    """Final agent output."""

    answer_markdown: str
    itinerary: ItineraryResult
    citations: list[Citation]
    tools_used: list[dict[str, Any]]
    decisions: list[str]  # Human-readable decision strings
    trace_id: str
    total_cost_usd: float
    execution_time_ms: int
