from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TicketFeedbackCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = None


class TicketFeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    rating: int
    comment: str | None = None
    created_at: datetime
    updated_at: datetime