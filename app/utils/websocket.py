from functools import lru_cache

from fastapi import WebSocket

from logger import logging_decorator


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    @logging_decorator()
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    @logging_decorator()
    async def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    @logging_decorator()
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)


@lru_cache()
def get_ws_manager() -> ConnectionManager:
    return ConnectionManager()
