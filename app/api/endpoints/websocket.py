from fastapi import APIRouter, Depends
from starlette.websockets import WebSocket, WebSocketDisconnect

from app.utils.websocket import ConnectionManager, get_ws_manager


ws_router = APIRouter()


@ws_router.websocket("/ws/tasks/")
async def subscribe_to_tasks(websocket: WebSocket, ws_manager: ConnectionManager = Depends(get_ws_manager)):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_json()

    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
