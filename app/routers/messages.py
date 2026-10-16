from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.security import get_current_user
from app.models.user import User
from app.models.ticket import Ticket
from app.models.message import TicketMessage
from app.models.agent import Agent
from app.schemas.message import MessageCreate, MessageResponse
from app.websockets.manager import manager

router = APIRouter(prefix="/tickets", tags=["Ticket Messages"])


async def check_ticket_access(
    ticket_id: int,
    current_user: User,
    db: AsyncSession,
) -> Ticket:
    result = await db.execute(
        select(Ticket).where(Ticket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    if current_user.role == "Customer":
        if ticket.customer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot access another customer's ticket",
            )

    elif current_user.role == "Agent":
        result = await db.execute(
            select(Agent).where(Agent.user_id == current_user.id)
        )
        agent = result.scalar_one_or_none()

        if agent is None or ticket.assigned_agent_id != agent.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can access only tickets assigned to you",
            )

    elif current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this ticket",
        )

    return ticket


@router.post(
    "/{ticket_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_message(
    ticket_id: int,
    data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await check_ticket_access(ticket_id, current_user, db)

    message_text = data.message.strip()

    if not message_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Message cannot be empty",
        )

    new_message = TicketMessage(
        ticket_id=ticket_id,
        sender_id=current_user.id,
        sender_role=current_user.role,
        message=message_text,
    )

    db.add(new_message)
    await db.commit()
    await db.refresh(new_message)

    
    await manager.broadcast(
        ticket_id,
        {
            "id": new_message.id,
            "ticket_id": new_message.ticket_id,
            "sender_id": new_message.sender_id,
            "sender_role": new_message.sender_role,
            "message": new_message.message,
            "created_at": new_message.created_at.isoformat(),
        },
    )

    return new_message


@router.get(
    "/{ticket_id}/messages",
    response_model=list[MessageResponse],
)
async def get_messages(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await check_ticket_access(ticket_id, current_user, db)

    result = await db.execute(
        select(TicketMessage)
        .where(
            TicketMessage.ticket_id == ticket_id,
            TicketMessage.is_internal_note.is_(False),
        )
        .order_by(TicketMessage.created_at.asc())
    )

    return result.scalars().all()