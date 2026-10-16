import pytest
from unittest.mock import AsyncMock

from app.websockets.manager import ConnectionManager


@pytest.mark.asyncio
async def test_connect_and_disconnect():
    manager = ConnectionManager()
    websocket = AsyncMock()

    await manager.connect(1, websocket)

    websocket.accept.assert_awaited_once()
    assert websocket in manager.active_connections[1]

    manager.disconnect(1, websocket)

    assert 1 not in manager.active_connections


@pytest.mark.asyncio
async def test_broadcast_to_connected_clients():
    manager = ConnectionManager()
    websocket = AsyncMock()

    await manager.connect(1, websocket)

    message = {"message": "Hello"}

    await manager.broadcast(1, message)

    websocket.send_json.assert_awaited_once_with(message)


@pytest.mark.asyncio
async def test_broadcast_without_connections():
    manager = ConnectionManager()

    await manager.broadcast(999, {"message": "Hello"})

    assert 999 not in manager.active_connections


@pytest.mark.asyncio
async def test_broadcast_removes_disconnected_client():
    manager = ConnectionManager()
    websocket = AsyncMock()

    await manager.connect(1, websocket)
    websocket.send_json.side_effect = RuntimeError("Connection lost")

    await manager.broadcast(1, {"message": "Hello"})

    assert 1 not in manager.active_connections