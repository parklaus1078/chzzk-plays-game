"""Queue state REST + WebSocket endpoints."""

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.dependencies import get_connection_manager, get_orchestrator
from app.services.connection_manager import ConnectionManager
from app.services.orchestrator import Orchestrator

router = APIRouter(prefix="/api", tags=["queue"])


@router.get("/queue")
async def get_queue(orchestrator: Orchestrator = Depends(get_orchestrator)):
    """Get current queue state (current + pending items)."""
    return orchestrator.get_queue_state()


@router.websocket("/ws/queue")
async def websocket_queue(
    websocket: WebSocket,
    manager: ConnectionManager = Depends(get_connection_manager),
    orchestrator: Orchestrator = Depends(get_orchestrator),
):
    """WebSocket endpoint for real-time queue updates.

    Sends initial state on connect, then broadcasts on every state change.
    """
    await manager.connect(websocket)
    try:
        # Send initial state immediately
        initial_state = orchestrator.get_queue_state()
        await websocket.send_json(initial_state.model_dump())

        # Keep connection alive
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
