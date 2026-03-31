import asyncio

import structlog
from fastapi import WebSocket

logger = structlog.get_logger()


class ConnectionManager:
    """WebSocket connection manager for broadcasting queue state to overlay UI.

    Single-process only. For multi-process, use encode/broadcaster.
    Automatically removes disconnected clients from the active list.
    """

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept WebSocket connection and add to active list."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("ws_client_connected", total=len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove WebSocket from active connections."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info("ws_client_disconnected", total=len(self.active_connections))

    async def broadcast(self, data: dict) -> None:
        """Broadcast data to all connected clients.

        Uses asyncio.gather with return_exceptions=True for concurrent sends.
        Automatically disconnects clients that fail to receive.
        """
        disconnected = []
        results = await asyncio.gather(
            *[conn.send_json(data) for conn in self.active_connections],
            return_exceptions=True,
        )
        for conn, result in zip(self.active_connections, results):
            if isinstance(result, Exception):
                logger.warning(
                    "ws_send_failed",
                    error=str(result),
                    error_type=type(result).__name__,
                )
                disconnected.append(conn)

        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
