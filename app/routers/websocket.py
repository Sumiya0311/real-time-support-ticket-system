from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.auth.security import get_websocket_user
from app.models.ticket import Ticket
from app.models.agent import Agent
from app.websockets.manager import manager

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/tickets/{ticket_id}")
async def ticket_websocket(
    websocket: WebSocket,
    ticket_id: int,
):
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=1008, reason="Authentication required")
        return

    async with AsyncSessionLocal() as db:
        user = await get_websocket_user(token, db)

        if user is None:
            await websocket.close(code=1008, reason="Invalid access token")
            return

        result = await db.execute(
            select(Ticket).where(Ticket.id == ticket_id)
        )
        ticket = result.scalar_one_or_none()

        if ticket is None:
            await websocket.close(code=1008, reason="Ticket not found")
            return

        allowed = False

        if user.role == "Admin":
            allowed = True

        elif user.role == "Customer":
            allowed = ticket.customer_id == user.id

        elif user.role == "Agent":
            result = await db.execute(
                select(Agent).where(Agent.user_id == user.id)
            )
            agent = result.scalar_one_or_none()

            allowed = (
                agent is not None
                and ticket.assigned_agent_id == agent.id
            )

        if not allowed:
            await websocket.close(
                code=1008,
                reason="You cannot access this ticket",
            )
            return

    await manager.connect(ticket_id, websocket)

    try:
        while True:
            
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(ticket_id, websocket)