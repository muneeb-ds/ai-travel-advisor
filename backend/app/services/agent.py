import json
import logging
import uuid
from datetime import datetime
from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.messages import ToolCall as LangchainToolCall
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.models.user import User
from app.repositories.knowledge_base import KnowledgeBaseRepository
from app.schemas.agent import (
    AgentRequest,
    AgentResponse,
    AgentState,
    Constraints,
    PlanList,
    StructuredItinerary,
    SynthesisResult,
    ToolUsage,
    Violation,
    WorkingSet,
)
from app.schemas.tools import (
    DailyWeather,
    EventSearchOutput,
    FlightSearchOutput,
    LodgingSearchOutput,
    WeatherOutput,
)
from app.services.tools import (
    currency_rates,
    events,
    flights,
    geocoding,
    knowledge_retrieval,
    lodging,
    transit,
    weather,
)

logger = logging.getLogger(__name__)


SYSTEM_MESSAGE = """
You are a travel advisor agent responsible for planning detailed itineraries by orchestrating multiple tools, including flights, lodging, events, transit, weather, currency, and retrieval-augmented generation (RAG) for knowledge.

Your responsibilities:
- Plan comprehensive, step-by-step travel itineraries that meet the user's goals and preferences.
- Use all available tools as needed to gather, verify, and cross-check information (e.g., book flights, find hotels, suggest events, check weather, convert currency, and retrieve relevant knowledge).
- Rigorously verify all plans against user-provided constraints (such as budget, timing, accessibility, or preferences).
- If any part of the plan violates constraints or fails, proactively repair the plan by re-planning or substituting alternatives.
- For each step in the itinerary, provide clear and structured output, including transparent citations for all information and tool results used.
- Ensure your final output is a structured itinerary, with each item annotated with its source or citation, and a log of all tool calls made.

Be proactive, thorough, and transparent in your reasoning and planning. Always ensure the user’s constraints are satisfied and explain any trade-offs or repairs made during planning.
"""

CONSTRAINT_EXTRACTION_PROMPT = """
Current Date: {current_date}

Extract all constraints from the user's query. For preferences, extract the preferences and their values. For example, if the user says "I want to go to the beach", the preference is "beach" and the value is "true".

user's query: {query}
"""

PLAN_PROMPT = """
Given the user's query and constraints, generate a detailed, step-by-step travel itinerary plan.

**Requirements:**

1.  **Extract Information**: Carefully read the user's query and the provided constraints. Use this information to fill in the arguments for each tool call.
2.  **Generate a Plan**: Create a multi-step plan as a JSON list of tool calls. You can use any of the available tools.
3.  **Specify Dependencies**: For each step, indicate if it depends on the completion of another step using `depends_on`.
4.  **Satisfy Constraints**: Ensure the generated plan satisfies all user constraints (e.g., budget, dates, preferences).
5.  **Output Format**: The output must be a JSON list of plan steps. Each step must have the following fields: `id`, `tool`, and `args`. `depends_on` is optional.

**Available Tools:**
{tool_schemas}

**User Constraints:**
{constraints}

**User Query:**
{query}
"""

REPAIR_PROMPT = """
The current travel itinerary plan has failed due to the following violations:
{violations}

Please generate a new plan that fixes these issues while still adhering to the original user query and constraints.

**Original User Query:**
{query}

**Original User Constraints:**
{constraints}

**Available Tools:**
{tool_schemas}
"""

SYNTHESIZER_PROMPT = """
Synthesize the user's query, constraints, and tool results into a coherent travel itinerary. Your main output should be a detailed, day-by-day itinerary in markdown format.

**User Query:**
{query}

**User Constraints:**
{constraints}

**Tool Results:**
{tool_results}

Generate a JSON object containing the following keys:
- `answer_markdown`: A detailed, day-by-day markdown-formatted travel itinerary. For each day, list the planned activities, including times, locations, and any relevant notes. Structure it clearly with headings for each day.
- `itinerary`: A structured itinerary with `days` and `total_cost_usd`. Each day should have a `date` and a list of `items`, where each item has `start`, `end`, `title`, `location`, and `notes`. This should be the machine-readable version of the itinerary in `answer_markdown`.
- `decisions`: A list of strings explaining any choices made, such as "Chose ITM over KIX due to shorter transfer time."

When generating the markdown itinerary, be sure to include citations for any information retrieved from the knowledge base. The citations are available in the `Tool Results` from the `knowledge_retrieval` tool.
"""


def should_repair(state: AgentState) -> Literal["repair_node", "router"]:
    if state.get("violations"):
        return "repair_node"
    return "router"


def is_refinement_check(
    state: AgentState,
) -> Literal["refinement_node", "constraint_extraction_node"]:
    if state.get("is_refinement"):
        return "refinement_node"
    return "constraint_extraction_node"


class AgentService:
    """Service for agent functionality."""

    def __init__(self, db: AsyncSession):
        self.graph = StateGraph(AgentState)
        self.knowledge_repo = KnowledgeBaseRepository(db)
        self.tools = [
            flights,
            lodging,
            geocoding,
            events,
            transit,
            weather,
            currency_rates,
            knowledge_retrieval,
        ]

    async def constraint_extraction_node(self, state: AgentState) -> AgentState:
        """Extract constraints from the user's request."""
        llm = ChatOpenAI(model="gpt-4o-mini", api_key=settings.OPENAI_API_KEY)

        # HumanMessage(content=CONSTRAINT_EXTRACTION_PROMPT.format(query=AgentState.messages[-1].content))

        constraints = await llm.with_structured_output(Constraints).ainvoke(state["messages"])
        state["constraints"] = constraints
        return state

    async def refinement_node(self, state: AgentState) -> AgentState:
        """If this is a refinement, update constraints based on the new query."""
        if not state.get("is_refinement"):
            return state

        llm = ChatOpenAI(model="gpt-4o-mini", api_key=settings.OPENAI_API_KEY)

        user_query = ""
        # Find the latest human message
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                user_query = msg.content
                break

        REFINEMENT_CONSTRAINT_EXTRACTION_PROMPT = """
        Current Date: {current_date}
        You are refining an existing travel plan. Here are the current constraints:
        {existing_constraints}

        The user has a new request:
        {query}

        Based on this new request, update the constraints. The new constraints should incorporate the refinement.
        For example, if the budget was $1000 and the request is "make it $200 cheaper", the new budget is $800.
        If a constraint is not mentioned, it should remain the same.
        Return the full, updated set of constraints.
        """
        prompt = REFINEMENT_CONSTRAINT_EXTRACTION_PROMPT.format(
            current_date=datetime.now().strftime("%Y-%m-%d"),
            existing_constraints=state.get("constraints"),
            query=user_query,
        )

        # We use the existing messages to provide context to the LLM, but we filter out
        # tool messages and the AIMessages that called them to avoid API errors.
        messages_for_refinement = []
        for msg in state["messages"]:
            if isinstance(msg, ToolMessage):
                continue
            if isinstance(msg, AIMessage) and msg.tool_calls:
                continue
            messages_for_refinement.append(msg)

        messages_with_refinement_prompt = messages_for_refinement + [HumanMessage(content=prompt)]

        updated_constraints = await llm.with_structured_output(Constraints).ainvoke(
            messages_with_refinement_prompt
        )

        state["constraints"] = updated_constraints

        # After updating constraints, we need to re-verify.
        # We can add a "dummy" violation to force the repair path.
        # The verifier_critic_node will run anyway and create proper violations.
        state["violations"] = [Violation(reason="User requested a refinement. Re-evaluating plan.")]

        return state

    def _format_tool_schemas(self) -> str:
        """Format tool schemas into a string for the prompt."""
        tool_schemas = []
        for tool in self.tools:
            args_schema = tool.args_schema.model_json_schema()

            # Filter out 'title' and 'type' from the main schema if they exist
            # and focus on properties
            if "properties" in args_schema:
                args_props = args_schema["properties"]
            else:
                args_props = {}

            schema = {
                "name": tool.name,
                "description": tool.description,
                "args": args_props,
            }
            tool_schemas.append(schema)
        return json.dumps(tool_schemas, indent=2)

    async def plan_node(self, state: AgentState) -> AgentState:
        """Plan the itinerary."""

        llm = ChatOpenAI(model="gpt-4o-mini", api_key=settings.OPENAI_API_KEY)

        tool_schemas = self._format_tool_schemas()

        # Create a new message for planning
        plan_message = HumanMessage(
            content=PLAN_PROMPT.format(
                constraints=state["constraints"],
                query=state["working_set"].query,
                tool_schemas=tool_schemas,
            )
        )

        # Add the planning message to the conversation
        messages_with_plan = state["messages"] + [plan_message]

        # Get the LLM response
        plan_response: dict = await llm.with_structured_output(
            PlanList.model_json_schema()
        ).ainvoke(messages_with_plan)

        state["plan"] = plan_response["plans"]
        state["messages"] = [
            plan_message,
            AIMessage(content=f"Generated plan with {len(plan_response['plans'])} steps"),
        ]
        # Return the new messages (plan_message + plan_response) to be added via add_messages reducer
        return state

    async def synthesizer_node(self, state: AgentState) -> AgentState:
        """Synthesize the plan and tool results into a coherent itinerary."""
        llm = ChatOpenAI(model="gpt-4o-mini", api_key=settings.OPENAI_API_KEY)

        tool_results = "\n".join(
            [
                f"Tool: {msg.name}\nContent: {msg.content}"
                for msg in state["messages"]
                if isinstance(msg, ToolMessage)
            ]
        )

        synthesis_message = HumanMessage(
            content=SYNTHESIZER_PROMPT.format(
                query=state["working_set"].query,
                constraints=state["constraints"],
                tool_results=tool_results,
            )
        )

        response = await llm.with_structured_output(SynthesisResult).ainvoke([synthesis_message])

        state["answer_markdown"] = response.answer_markdown
        state["itinerary"] = response.itinerary
        state["decisions"] = response.decisions

        return state

    async def responder_node(self, state: AgentState) -> AgentState:
        """Prepare the final response for the user."""
        response_message = AIMessage(
            content=state.get("answer_markdown", "Here is your travel plan.")
        )
        return {"messages": [response_message]}

    async def repair_node(self, state: AgentState) -> AgentState:
        """Repair the plan based on violations."""
        llm = ChatOpenAI(model="gpt-4o-mini", api_key=settings.OPENAI_API_KEY)
        tool_schemas = self._format_tool_schemas()

        violations_str = "\n".join([v.reason for v in state["violations"]])

        repair_message = HumanMessage(
            content=REPAIR_PROMPT.format(
                violations=violations_str,
                query=state["working_set"].query,
                constraints=state["constraints"],
                tool_schemas=tool_schemas,
            )
        )

        # Filter out the previous tool messages and the AI message that called them
        messages_for_repair = []
        for msg in state["messages"]:
            if isinstance(msg, ToolMessage):
                continue
            if isinstance(msg, AIMessage) and msg.tool_calls:
                continue
            messages_for_repair.append(msg)

        messages_with_repair = messages_for_repair + [repair_message]
        plan_response: dict = await llm.with_structured_output(
            PlanList.model_json_schema()
        ).ainvoke(messages_with_repair)

        # Reset violations and update plan
        state["violations"] = []
        state["plan"] = plan_response["plans"]
        state["messages"] = messages_for_repair + [
            repair_message,
            AIMessage(content=f"Repaired plan with {len(plan_response['plans'])} steps"),
        ]

        return state

    async def verifier_critic_node(self, state: AgentState) -> AgentState:
        """Verify the plan against constraints and add violations."""
        state["violations"] = []
        constraints = state.get("constraints")
        tool_messages = [msg for msg in state["messages"] if isinstance(msg, ToolMessage)]

        parsed_tool_outputs = {}
        model_map = {
            "flights": FlightSearchOutput,
            "lodging": LodgingSearchOutput,
            "events": EventSearchOutput,
            "weather": WeatherOutput,
        }

        for msg in tool_messages:
            if msg.name in model_map:
                try:
                    parsed_output = model_map[msg.name].model_validate_json(msg.content)
                    if msg.name not in parsed_tool_outputs:
                        parsed_tool_outputs[msg.name] = []
                    parsed_tool_outputs[msg.name].append(parsed_output)
                except Exception:
                    logger.warning(f"Could not parse tool output for {msg.name}: {msg.content}")

        # 1. Budget Check
        if constraints and constraints.budget_usd:
            total_cost = 0
            if "flights" in parsed_tool_outputs:
                for output in parsed_tool_outputs["flights"]:
                    total_cost += sum(f.price for f in output.flights)

            if "lodging" in parsed_tool_outputs and constraints.dates:
                num_days = (constraints.dates.end - constraints.dates.start).days
                for output in parsed_tool_outputs["lodging"]:
                    total_cost += sum(l.price_per_night * num_days for l in output.lodging_options)

            if total_cost > constraints.budget_usd:
                state["violations"].append(
                    Violation(
                        reason=f"Budget exceeded: Total cost ${total_cost} is over the budget of ${constraints.budget_usd}"
                    )
                )

        # 2. Feasibility Check (e.g., no overnight flights)
        if (
            constraints
            and constraints.preferences
            and constraints.preferences.get("no_overnight_flights")
        ):
            if "flights" in parsed_tool_outputs:
                for output in parsed_tool_outputs["flights"]:
                    for flight in output.flights:
                        departure_time = datetime.fromisoformat(flight.departure_time).time()
                        arrival_time = datetime.fromisoformat(flight.arrival_time).time()
                        if departure_time.hour > 22 or arrival_time.hour < 6:
                            state["violations"].append(
                                Violation(
                                    reason=f"Constraint violation: Plan includes an overnight flight ({flight.flight_number}) against user preference."
                                )
                            )

        # 3. Weather Sensitivity
        weather_forecasts: list[DailyWeather] = []
        if "weather" in parsed_tool_outputs:
            for output in parsed_tool_outputs["weather"]:
                weather_forecasts.extend(output.daily)

        rainy_days = {
            f.forecast_date
            for f in weather_forecasts
            if f.weather_code in [51, 53, 55, 61, 63, 65, 80, 81, 82]
        }

        if rainy_days and "events" in parsed_tool_outputs:
            for output in parsed_tool_outputs["events"]:
                for event in output.events:
                    if not event.is_indoor:
                        state["violations"].append(
                            Violation(
                                reason=f"Weather sensitivity: Event '{event.name}' is on a rainy day. Consider an indoor alternative."
                            )
                        )

        # 4. Preference Fit (e.g., kid-friendly)
        if constraints and constraints.preferences:
            kid_friendly_pref = constraints.preferences.get("kid_friendly")
            if kid_friendly_pref is not None and "events" in parsed_tool_outputs:
                for output in parsed_tool_outputs["events"]:
                    for event in output.events:
                        if kid_friendly_pref and not event.kid_friendly:
                            state["violations"].append(
                                Violation(
                                    reason=f"Preference violation: Event '{event.name}' is not kid-friendly, but this was a user preference."
                                )
                            )

        return state

    def _get_completed_step_ids(self, state: AgentState) -> set[str]:
        """Get the IDs of completed plan steps from tool messages."""
        completed_ids = set()
        for message in state["messages"]:
            if isinstance(message, ToolMessage) and message.tool_call_id:
                completed_ids.add(message.tool_call_id)
        return completed_ids

    async def router_node(self, state: AgentState) -> AgentState:
        """
        Determines the next steps to execute from the plan and adds them as tool calls
        to a new AIMessage.
        """
        completed_step_ids = self._get_completed_step_ids(state)
        plan = state.get("plan", [])

        runnable_steps = []
        for step in plan:
            if step.get("id") not in completed_step_ids:
                if not step.get("depends_on") or set(step.get("depends_on")).issubset(
                    completed_step_ids
                ):
                    runnable_steps.append(step)

        if not runnable_steps:
            return state

        tool_calls = [
            LangchainToolCall(name=step.get("tool"), args=step.get("args"), id=step.get("id"))
            for step in runnable_steps
        ]

        ai_message = AIMessage(content="", tool_calls=tool_calls)
        return {"messages": [ai_message]}

    async def add_nodes_and_edges(self):
        """Add nodes to the graph."""

        tool_node = ToolNode(self.tools)

        self.graph.add_node("constraint_extraction_node", self.constraint_extraction_node)
        self.graph.add_node("plan_node", self.plan_node)
        self.graph.add_node("router", self.router_node)
        # self.graph.add_node("tool_executor", self.tool_nodes_with_tracking)
        self.graph.add_node("tool_executor", tool_node)
        self.graph.add_node("verifier_critic_node", self.verifier_critic_node)
        self.graph.add_node("repair_node", self.repair_node)
        self.graph.add_node("synthesizer_node", self.synthesizer_node)
        self.graph.add_node("responder_node", self.responder_node)
        self.graph.add_node("refinement_node", self.refinement_node)

        self.graph.add_conditional_edges(
            START,
            is_refinement_check,
            {
                "refinement_node": "refinement_node",
                "constraint_extraction_node": "constraint_extraction_node",
            },
        )
        self.graph.add_edge("refinement_node", "verifier_critic_node")
        self.graph.add_edge("constraint_extraction_node", "plan_node")
        self.graph.add_edge("plan_node", "router")
        self.graph.add_conditional_edges(
            "router",
            tools_condition,
            {
                "tools": "tool_executor",
                "__end__": "synthesizer_node",
            },
        )
        self.graph.add_edge("tool_executor", "verifier_critic_node")
        self.graph.add_conditional_edges(
            "verifier_critic_node",
            should_repair,
            {
                "repair_node": "repair_node",
                "router": "router",
            },
        )
        self.graph.add_edge("repair_node", "router")
        self.graph.add_edge("synthesizer_node", "responder_node")
        self.graph.add_edge("responder_node", END)
        return self.graph

    async def plan_itinerary(self, user: User, agent_request: AgentRequest):
        """Generate an itinerary plan using LangGraph."""
        knowledge_items = await self.knowledge_repo.get_all_visible(user.id, user.org_id)

        knowledge_item_ids = [str(knowledge_item.id) for knowledge_item in knowledge_items]

        await self.add_nodes_and_edges()

        # Compile graph with checkpointer
        async with AsyncPostgresSaver.from_conn_string(
            settings.DATABASE_URL.replace("+asyncpg", "")
        ) as checkpointer:
            await checkpointer.setup()
            compiled_graph: CompiledStateGraph = self.graph.compile(checkpointer=checkpointer)

            thread_id = agent_request.thread_id or str(uuid.uuid4())
            config = {"configurable": {"thread_id": thread_id}}

            is_refinement = False
            if agent_request.thread_id:
                # Check if a state already exists for this thread
                existing_state = await compiled_graph.aget_state(config)
                if existing_state and existing_state.values.get("itinerary"):
                    is_refinement = True

            if is_refinement:
                # For a refinement, we just pass the new message and the refinement flag
                input_data = {
                    "messages": [HumanMessage(content=agent_request.query)],
                    "is_refinement": True,
                }
            else:
                # For a new plan, we set up the initial state
                input_data = {
                    "messages": [
                        SystemMessage(content=SYSTEM_MESSAGE),
                        HumanMessage(content=agent_request.query),
                    ],
                    "working_set": WorkingSet(
                        knowledge_item_ids=knowledge_item_ids, query=agent_request.query
                    ),
                    "constraints": Constraints(),
                    "plan": [],
                    "citations": [],
                    "tool_calls": [],
                    "violations": [],
                    "budget_counters": {},
                    "answer_markdown": None,
                    "itinerary": None,
                    "decisions": [],
                    "done": False,
                    "is_refinement": False,
                }

            # Stream intermediate steps
            async for chunk in compiled_graph.astream(input_data, config=config):
                for node, update in chunk.items():
                    print("Update from node", node)
                    if "messages" in update and update["messages"]:
                        update["messages"][-1].pretty_print()

            # Get the final state from the checkpointer
            final_state_snapshot = await compiled_graph.aget_state(config)
            final_state = final_state_snapshot.values if final_state_snapshot else {}

            tool_calls = final_state.get("tool_calls", [])
            tool_usage = []
            if tool_calls:
                tool_counts = {}
                for tc in tool_calls:
                    if tc.name not in tool_counts:
                        tool_counts[tc.name] = {"count": 0, "total_ms": 0}
                    tool_counts[tc.name]["count"] += 1
                    tool_counts[tc.name]["total_ms"] += tc.time_ms

                tool_usage = [
                    ToolUsage(name=name, count=data["count"], total_ms=data["total_ms"])
                    for name, data in tool_counts.items()
                ]

            return AgentResponse(
                answer_markdown=final_state.get("answer_markdown", ""),
                itinerary=final_state.get("itinerary") or StructuredItinerary(days=[]),
                citations=final_state.get("citations", []),
                tools_used=tool_usage,
                decisions=final_state.get("decisions", []),
            )
