from typing import Any

from pydantic import BaseModel

# from app.schemas.agent_graph import AgentCreate


class AgentState(BaseModel):
    """Typed state for the LangGraph agent."""

    messages: list[dict[str, Any]] = []
    constraints: dict[str, Any] = {}
    plan: list[dict[str, Any]] = []
    working_set: dict[str, Any] = {}
    citations: list[dict[str, Any]] = []
    tool_calls: list[dict[str, Any]] = []
    violations: list[dict[str, Any]] = []
    budget_counters: dict[str, Any] = {}
    done: bool = False


# class AgentService:
#     """Service for agent functionality."""

#     # def __init__(self, db: AsyncSession):
#     # self.agent_repo = AgentRepository(db)

#     async def create_agent(self, agent_data: AgentCreate) -> Agent:
#         """Create a new agent."""
#         return await self.agent_repo.create(agent_data)
