import logging

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)

from app.api.dependencies import get_agent_service, get_current_user
from app.core.limiter import limiter
from app.models.user import User
from app.schemas.agent import AgentRequest, AgentResponse
from app.services.agent import AgentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/qa", tags=["agent"])


@router.post("/plan", response_model=AgentResponse)
@limiter.limit("5/minute")
async def plan_itinerary(
    request: Request,  # noqa: ARG001
    agent_request: AgentRequest,
    user: User = Depends(get_current_user),  # noqa: ARG001
    agent_service: AgentService = Depends(get_agent_service),
):
    """
    Generate an itinerary plan using LangGraph agent (non-streaming).
    Returns: AI response, citations, and tool calls log.
    """
    try:
        response = await agent_service.plan_itinerary(user, agent_request)
        return response
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate itinerary: {str(e)}",
        )


@router.websocket("/stream")
async def qa_stream(
    websocket: WebSocket,
    user: User = Depends(get_current_user),  # noqa: ARG001
):
    """
    WebSocket endpoint for streaming itinerary planning progress and final payload.
    """
    await websocket.accept()
    try:
        # Placeholder: Replace with actual streaming logic
        import asyncio

        for i in range(3):
            await websocket.send_text(f"Progress: {i+1}/3")
            await asyncio.sleep(1)
        await websocket.send_text('{"itinerary": {}, "citations": [], "tool_log": []}')
        await websocket.close()
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.close(code=1011, reason=str(e))
