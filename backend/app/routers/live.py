"""WebSocket routes for live metric streaming."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.services import live_metrics_stream

router = APIRouter()


@router.websocket("/live")
async def live_metrics(websocket: WebSocket) -> None:
    await websocket.accept()
    queue = live_metrics_stream.subscribe()
    try:
        while True:
            payload = await queue.get()
            await websocket.send_json(payload)
    except WebSocketDisconnect:
        pass
    finally:
        live_metrics_stream.unsubscribe(queue)


