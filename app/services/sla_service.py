from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ticket import Ticket


async def check_sla_breaches(db: AsyncSession) -> int:
    """
    Mark tickets as SLA-breached when either deadline has passed.
    Returns the number of tickets newly marked as breached.
    """
    now = datetime.utcnow()

    result = await db.execute(
        select(Ticket).where(
            Ticket.status.notin_(["Resolved", "Closed"]),
            Ticket.sla_breached.is_(False),
        )
    )

    tickets = result.scalars().all()
    breached_count = 0

    for ticket in tickets:
        first_response_missed = (
            ticket.first_response_due is not None
            and ticket.first_response_at is None
            and ticket.first_response_due <= now
        )

        resolution_missed = (
            ticket.resolution_due is not None
            and ticket.resolution_due <= now
        )

        if first_response_missed or resolution_missed:
            ticket.sla_breached = True
            breached_count += 1

    if breached_count:
        await db.commit()

    return breached_count