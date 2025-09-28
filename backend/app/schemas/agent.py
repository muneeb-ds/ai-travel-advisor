from collections.abc import Sequence
from datetime import date
from operator import add
from typing import Annotated, Any

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel
from typing_extensions import TypedDict


class Dates(BaseModel):
    start: date
    end: date


class Constraints(BaseModel):
    budget_usd: int | None = None
    dates: Dates | None = None
    airports: list[str | None] = []
    preferences: dict[str, bool] | None = {}


class Plan(BaseModel):
    id: str
    tool: str
    args: dict = {}
    depends_on: list[str] = []
    cost_estimate: float = 0
    time_estimate: float = 0


class PlanList(BaseModel):
    plans: list[Plan]


class Violation(BaseModel):
    reason: str
    conflicting_steps: list[str] = []


class ItineraryItem(BaseModel):
    start: str | None = ""
    end: str | None = ""
    title: str
    location: str | None = ""
    notes: str | None = ""


class ItineraryDay(BaseModel):
    date: str
    items: list[ItineraryItem]


class StructuredItinerary(BaseModel):
    days: list[ItineraryDay]
    total_cost_usd: float = 0.0


class Citation(BaseModel):
    title: str
    source: str  # "url|manual|file|tool"
    ref: str  # "knowledge_id or tool_name#id"


class ToolUsage(BaseModel):
    name: str
    count: int
    total_ms: int


class SynthesisResult(BaseModel):
    answer_markdown: str
    itinerary: StructuredItinerary
    decisions: list[str] = []


class WorkingSet(BaseModel):
    knowledge_item_ids: list[str]
    query: str


class ToolCall(BaseModel):
    """Schema for tool call information."""

    name: str
    args: dict[str, Any]
    time_ms: int


class AgentState(TypedDict):
    """Typed state for the LangGraph agent."""

    messages: Annotated[Sequence[AnyMessage], add_messages]
    constraints: Constraints
    plan: Annotated[list[Plan], add] = []
    working_set: WorkingSet
    citations: Annotated[list[Citation], add]
    tool_calls: Annotated[list[ToolCall], add]
    violations: Annotated[list[Violation], add]
    budget_counters: dict[str, Any]
    answer_markdown: str | None
    itinerary: StructuredItinerary | None
    decisions: Annotated[list[str], add]
    done: bool
    is_refinement: bool


class AgentRequest(BaseModel):
    """Request schema for agent planning."""

    query: str
    thread_id: str | None = None


class AgentResponse(BaseModel):
    """Response schema for agent planning."""

    answer_markdown: str
    itinerary: StructuredItinerary
    citations: list[Citation] = []
    tools_used: list[ToolUsage] = []
    decisions: list[str] = []
