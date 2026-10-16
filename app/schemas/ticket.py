from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


class TicketCreate(BaseModel):
    category_id: int = Field(gt=0)
    subject: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=5)
    priority: Literal["Low", "Medium", "High", "Urgent"] = "Medium"


class TicketResponse(BaseModel):
    id: int
    ticket_number: str
    customer_id: int
    category_id: int
    assigned_agent_id: int | None
    subject: str
    description: str
    priority: str
    status: str
    first_response_due: datetime | None
    resolution_due: datetime | None
    first_response_at: datetime | None
    resolved_at: datetime | None
    closed_at: datetime | None
    sla_breached: bool
    reopen_count: int

    model_config = ConfigDict(from_attributes=True)
class TicketStatusUpdate(BaseModel):
    status: Literal[
        "Open",
        "Assigned",
        "In Progress",
        "Waiting on Customer",
        "Resolved",
        "Closed",
    ]

class TicketAssignRequest(BaseModel):
    agent_id: int = Field(gt=0)