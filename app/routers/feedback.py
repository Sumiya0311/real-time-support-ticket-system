from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.security import get_current_user
from app.models.user import User
from app.models.ticket import Ticket
from app.models.ticket_feedback import TicketFeedback
from app.schemas.feedback import (
    TicketFeedbackCreate,
    TicketFeedbackResponse,
)

router = APIRouter(
    prefix="/feedback",
    tags=["Feedback and Ratings"],
)


@router.post(
    "/tickets/{ticket_id}",
    response_model=TicketFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_ticket_feedback(
    ticket_id: int,
    payload: TicketFeedbackCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Only customers can submit feedback
    if current_user.role != "Customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can submit ticket feedback",
        )

    result = await db.execute(
        select(Ticket).where(Ticket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    if ticket.customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only rate your own tickets",
        )

    if ticket.status not in ("Resolved", "Closed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feedback can only be submitted for resolved or closed tickets",
        )

    existing_result = await db.execute(
        select(TicketFeedback).where(
            TicketFeedback.ticket_id == ticket_id
        )
    )

    if existing_result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Feedback has already been submitted for this ticket",
        )

    feedback = TicketFeedback(
        ticket_id=ticket_id,
        rating=payload.rating,
        comment=payload.comment,
    )

    db.add(feedback)

    try:
        await db.commit()
        await db.refresh(feedback)
    except Exception:
        await db.rollback()
        raise

    return feedback


@router.get(
    "/tickets/{ticket_id}",
    response_model=TicketFeedbackResponse,
)
async def get_ticket_feedback(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket_result = await db.execute(
        select(Ticket).where(Ticket.id == ticket_id)
    )
    ticket = ticket_result.scalar_one_or_none()

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    # Customers can view feedback only for their own tickets.
    # Admins and agents can view feedback for an existing ticket.
    if (
        current_user.role == "Customer"
        and ticket.customer_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot view feedback for another customer's ticket",
        )

    result = await db.execute(
        select(TicketFeedback).where(
            TicketFeedback.ticket_id == ticket_id
        )
    )
    feedback = result.scalar_one_or_none()

    if feedback is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found for this ticket",
        )

    return feedback