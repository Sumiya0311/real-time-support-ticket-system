from pydantic import BaseModel, Field


class TicketSummaryReport(BaseModel):
    total_tickets: int = Field(ge=0)
    tickets_by_status: dict[str, int]
    tickets_by_priority: dict[str, int]