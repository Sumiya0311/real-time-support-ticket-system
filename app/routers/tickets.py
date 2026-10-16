import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.security import get_current_user
from app.models.user import User
from app.models.agent import Agent
from app.models.category import Category
from app.models.ticket import Ticket
from app.models.ticket_history import TicketHistory
from app.models.notification import Notification
from app.models.sla_policy import SLAPolicy
from app.services.email_service import send_email
from app.schemas.ticket import (
    TicketCreate,
    TicketResponse,
    TicketStatusUpdate,
    TicketAssignRequest,
)

router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"],
)

OPEN_STATUSES = [
    "Open",
    "Assigned",
    "In Progress",
    "Waiting on Customer",
]


# 1. Create a ticket with SLA deadlines
@router.post(
    "/",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_ticket(
    payload: TicketCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    category_result = await db.execute(
        select(Category).where(
            Category.id == payload.category_id,
            Category.is_active.is_(True),
        )
    )
    category = category_result.scalar_one_or_none()

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active category not found",
        )

    sla_result = await db.execute(
        select(SLAPolicy).where(
            SLAPolicy.priority == payload.priority
        )
    )
    sla_policy = sla_result.scalar_one_or_none()

    if sla_policy is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No SLA policy found for priority: {payload.priority}",
        )

    now = datetime.utcnow()

    ticket = Ticket(
        ticket_number=f"TKT-{uuid.uuid4().hex[:12].upper()}",
        customer_id=current_user.id,
        category_id=payload.category_id,
        subject=payload.subject,
        description=payload.description,
        priority=payload.priority,
        status="Open",
        first_response_due=now + timedelta(
            minutes=sla_policy.first_response_minutes
        ),
        resolution_due=now + timedelta(
            minutes=sla_policy.resolution_minutes
        ),
    )

    db.add(ticket)

    try:
        await db.flush()

        db.add(
            TicketHistory(
                ticket_id=ticket.id,
                old_status=None,
                new_status="Open",
                changed_by=current_user.id,
                change_reason="Ticket created",
            )
        )

        db.add(
            Notification(
                user_id=current_user.id,
                ticket_id=ticket.id,
                title="Ticket Created",
                message=(
                    f"Your ticket {ticket.ticket_number} "
                    "has been created successfully."
                ),
                notification_type="ticket_created",
                is_read=False,
            )
        )

        await db.commit()
        await db.refresh(ticket)

    except Exception:
        await db.rollback()
        raise

    try:
        send_email(
            to_email=current_user.email,
            subject=f"Ticket Created: {ticket.ticket_number}",
            body=(
                f"Hello {current_user.email},\n\n"
                "Your support ticket has been created successfully.\n"
                f"Ticket Number: {ticket.ticket_number}\n"
                f"Subject: {ticket.subject}\n"
                f"Priority: {ticket.priority}\n"
                f"Status: {ticket.status}\n"
                f"First response due: {ticket.first_response_due}\n"
                f"Resolution due: {ticket.resolution_due}\n\n"
                "Thank you for contacting support."
            ),
        )
    except Exception as exc:
        print(f"Could not send ticket confirmation email: {exc}")

    return ticket


# 2. List, search, filter, sort, and paginate tickets
@router.get(
    "/",
    response_model=list[TicketResponse],
)
async def list_tickets(
    search: str | None = Query(default=None, max_length=200),
    ticket_status: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    sort_by: str = Query(default="id"),
    sort_order: str = Query(default="desc"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    allowed_sort_columns = {
        "id": Ticket.id,
        "priority": Ticket.priority,
        "status": Ticket.status,
    }

    if hasattr(Ticket, "created_at"):
        allowed_sort_columns["created_at"] = Ticket.created_at

    if sort_by not in allowed_sort_columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid sort_by field. Allowed fields: "
                + ", ".join(allowed_sort_columns.keys())
            ),
        )

    if sort_order not in ("asc", "desc"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="sort_order must be asc or desc",
        )

    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date cannot be after end_date",
        )

    query = select(Ticket)

    if current_user.role == "Customer":
        query = query.where(
            Ticket.customer_id == current_user.id
        )

    elif current_user.role == "Agent":
        agent_result = await db.execute(
            select(Agent).where(
                Agent.user_id == current_user.id
            )
        )
        agent = agent_result.scalar_one_or_none()

        if agent is None:
            return []

        query = query.where(
            Ticket.assigned_agent_id == agent.id
        )

    if search and search.strip():
        search_term = f"%{search.strip()}%"

        search_conditions = [
            Ticket.subject.ilike(search_term),
            Ticket.description.ilike(search_term),
        ]

        if hasattr(Ticket, "ticket_number"):
            search_conditions.append(
                Ticket.ticket_number.ilike(search_term)
            )

        query = query.where(or_(*search_conditions))

    if ticket_status:
        query = query.where(Ticket.status == ticket_status)

    if priority:
        query = query.where(Ticket.priority == priority)

    if start_date or end_date:
        if not hasattr(Ticket, "created_at"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Date filtering is not supported by the ticket model",
            )

        if start_date:
            query = query.where(Ticket.created_at >= start_date)

        if end_date:
            query = query.where(Ticket.created_at <= end_date)

    sort_column = allowed_sort_columns[sort_by]

    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


# 3. Retrieve a ticket by ID
@router.get(
    "/{ticket_id}",
    response_model=TicketResponse,
)
async def get_ticket(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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
        agent_result = await db.execute(
            select(Agent).where(
                Agent.user_id == current_user.id
            )
        )
        agent = agent_result.scalar_one_or_none()

        if (
            agent is None
            or ticket.assigned_agent_id != agent.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot access this ticket",
            )

    return ticket


# 4. Update ticket status and record history
@router.patch(
    "/{ticket_id}/status",
    response_model=TicketResponse,
)
async def update_ticket_status(
    ticket_id: int,
    payload: TicketStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("Admin", "Agent"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and agents can update ticket status",
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

    if current_user.role == "Agent":
        agent_result = await db.execute(
            select(Agent).where(
                Agent.user_id == current_user.id
            )
        )
        agent = agent_result.scalar_one_or_none()

        if (
            agent is None
            or ticket.assigned_agent_id != agent.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update tickets assigned to you",
            )

    old_status = ticket.status
    new_status = payload.status

    if old_status == new_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ticket already has this status",
        )

    now = datetime.utcnow()
    ticket.status = new_status

    if new_status == "Resolved":
        ticket.resolved_at = now
    elif new_status == "Closed":
        ticket.closed_at = now

    db.add(
        TicketHistory(
            ticket_id=ticket.id,
            old_status=old_status,
            new_status=new_status,
            changed_by=current_user.id,
            change_reason="Status updated through the API",
        )
    )

    try:
        await db.commit()
        await db.refresh(ticket)
    except Exception:
        await db.rollback()
        raise

    return ticket


# 5. View ticket status history
@router.get("/{ticket_id}/history")
async def get_ticket_history(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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
                detail="You cannot access another customer's ticket history",
            )

    elif current_user.role == "Agent":
        agent_result = await db.execute(
            select(Agent).where(
                Agent.user_id == current_user.id
            )
        )
        agent = agent_result.scalar_one_or_none()

        if (
            agent is None
            or ticket.assigned_agent_id != agent.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot access this ticket history",
            )

    history_result = await db.execute(
        select(TicketHistory)
        .where(TicketHistory.ticket_id == ticket_id)
        .order_by(TicketHistory.changed_at.asc())
    )

    records = history_result.scalars().all()

    return [
        {
            "id": record.id,
            "ticket_id": record.ticket_id,
            "old_status": record.old_status,
            "new_status": record.new_status,
            "changed_by": record.changed_by,
            "change_reason": record.change_reason,
            "changed_at": record.changed_at,
        }
        for record in records
    ]


# 6. Assign a ticket to an agent (Admin only)
@router.patch(
    "/{ticket_id}/assign",
    response_model=TicketResponse,
)
async def assign_ticket(
    ticket_id: int,
    payload: TicketAssignRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can assign tickets",
        )

    ticket_result = await db.execute(
        select(Ticket).where(Ticket.id == ticket_id)
    )
    ticket = ticket_result.scalar_one_or_none()

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    agent_result = await db.execute(
        select(Agent).where(Agent.id == payload.agent_id)
    )
    agent = agent_result.scalar_one_or_none()

    if agent is None or not agent.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active agent not found",
        )

    if agent.availability != "Online":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Agent must be online to receive tickets",
        )

    count_result = await db.execute(
        select(func.count(Ticket.id)).where(
            Ticket.assigned_agent_id == agent.id,
            Ticket.status.in_(OPEN_STATUSES),
            Ticket.id != ticket.id,
        )
    )
    open_ticket_count = count_result.scalar_one()

    if open_ticket_count >= agent.max_open_tickets:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Agent has reached their open-ticket capacity",
        )

    old_status = ticket.status
    old_agent_id = ticket.assigned_agent_id

    ticket.assigned_agent_id = agent.id

    if ticket.status == "Open":
        ticket.status = "Assigned"

    db.add(
        TicketHistory(
            ticket_id=ticket.id,
            old_status=old_status,
            new_status=ticket.status,
            changed_by=current_user.id,
            change_reason=(
                f"Assigned to agent {agent.id}; "
                f"previous agent: {old_agent_id}"
            ),
        )
    )

    try:
        await db.commit()
        await db.refresh(ticket)
    except Exception:
        await db.rollback()
        raise

    return ticket