import asyncio
import json
import threading
import time

import pytest
import uvicorn
import websockets
from websockets import ConnectionClosedOK

from app.utils.websocket import get_ws_manager
from main import app


SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000
ws_url = f"ws://{SERVER_HOST}:{SERVER_PORT}/ws/tasks/"


def run_uvicorn_server():
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)


@pytest.fixture(scope="module", autouse=True)
def start_server():
    server_thread = threading.Thread(target=run_uvicorn_server, daemon=True)
    server_thread.start()
    time.sleep(1)
    yield


@pytest.mark.asyncio
async def test_websocket_broadcast():
    message = {"status": "updated"}
    ws_manager = get_ws_manager()

    async with websockets.connect(ws_url) as ws_client:
        await asyncio.sleep(1)
        await ws_manager.broadcast(message)

        received_raw = await ws_client.recv()
        received_msg = json.loads(received_raw)

        assert len(ws_manager.active_connections) == 1

    assert received_msg == message


@pytest.mark.asyncio
async def test_websocket_broadcast_multiple_connections():
    message = {"status": "updated"}
    ws_manager = get_ws_manager()

    async with websockets.connect(ws_url) as first_ws, websockets.connect(ws_url) as second_ws:
        await ws_manager.broadcast(message)
        first_raw = await first_ws.recv()
        first_msg = json.loads(first_raw)
        second_raw = await second_ws.recv()
        second_msg = json.loads(second_raw)

        assert len(ws_manager.active_connections) == 2

    assert first_msg == message
    assert second_msg == message


@pytest.mark.asyncio
async def test_websocket_broadcast_disconnect():
    message = {"status": "updated"}
    ws_manager = get_ws_manager()
    exc_type = ConnectionClosedOK

    async with websockets.connect(ws_url) as first_client:
        async with websockets.connect(ws_url) as second_client:
            pass

        await ws_manager.broadcast(message)

        first_raw = await first_client.recv()
        first_msg = json.loads(first_raw)

        with pytest.raises(exc_type) as exc_info:
            await second_client.recv()

        assert first_msg == message
        assert exc_info.type is exc_type


@pytest.mark.asyncio
async def test_websocket_broadcast_multiple_messages():
    messages = [{"status": "updated"}, {"status": "completed"}]
    ws_manager = get_ws_manager()

    async with websockets.connect(ws_url) as ws_client:
        for message in messages:
            await ws_manager.broadcast(message)

        for message in messages:
            cur_raw = await ws_client.recv()
            cur_msg = json.loads(cur_raw)
            assert cur_msg == message
