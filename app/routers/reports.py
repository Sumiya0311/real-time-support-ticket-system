from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.ticket import Ticket
from app.schemas.report import TicketSummaryReport

router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


@router.get(
    "/summary",
    response_model=TicketSummaryReport,
)
async def get_ticket_summary(
    db: AsyncSession = Depends(get_db),
):
    # Total number of tickets
    total_result = await db.execute(
        select(func.count(Ticket.id))
    )
    total_tickets = total_result.scalar() or 0

    # Count tickets grouped by status
    status_result = await db.execute(
        select(
            Ticket.status,
            func.count(Ticket.id),
        ).group_by(Ticket.status)
    )

    tickets_by_status = {
        str(status.value if hasattr(status, "value") else status): count
        for status, count in status_result.all()
    }

    # Count tickets grouped by priority
    priority_result = await db.execute(
        select(
            Ticket.priority,
            func.count(Ticket.id),
        ).group_by(Ticket.priority)
    )

    tickets_by_priority = {
        str(priority.value if hasattr(priority, "value") else priority): count
        for priority, count in priority_result.all()
    }

    return TicketSummaryReport(
        total_tickets=total_tickets,
        tickets_by_status=tickets_by_status,
        tickets_by_priority=tickets_by_priority,
    )