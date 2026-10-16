from typing import Dict, Set

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, ticket_id: int, websocket: WebSocket):
        await websocket.accept()

        if ticket_id not in self.active_connections:
            self.active_connections[ticket_id] = set()

        self.active_connections[ticket_id].add(websocket)

    def disconnect(self, ticket_id: int, websocket: WebSocket):
        connections = self.active_connections.get(ticket_id)

        if connections:
            connections.discard(websocket)

            if not connections:
                self.active_connections.pop(ticket_id, None)

    async def broadcast(self, ticket_id: int, message: dict):
        connections = self.active_connections.get(ticket_id, set())

        disconnected = []

        for websocket in connections.copy():
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)

        for websocket in disconnected:
            self.disconnect(ticket_id, websocket)


manager = ConnectionManager()