from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)

from app.api.dependencies import get_current_user
from app.core.limiter import limiter
from app.models.user import User

router = APIRouter(prefix="/qa", tags=["agent"])


@router.post("/plan")
@limiter.limit("5/minute")
async def plan_itinerary(
    request: Request, # noqa: ARG001
    request_data: dict, # noqa: ARG001
    user: User = Depends(get_current_user) # noqa: ARG001
):
    """
    Generate an itinerary plan (non-streaming).
    Returns: itinerary JSON, citations, and tool log.

    Supports idempotency via the Idempotency-Key header. If the same key is used
    within the TTL window, the original response will be returned.
    """
    # Placeholder: Replace with actual planning logic
    try:
        # Example response structure
        response = {"itinerary": {"days": []}, "citations": [], "tool_log": []}
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate itinerary: {str(e)}",
        )


@router.websocket("/stream")
async def qa_stream(
    websocket: WebSocket,
    user: User = Depends(get_current_user) # noqa: ARG001
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
