from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class MessageCreate(BaseModel):
    message: str = Field(min_length=1, max_length=5000)


class MessageResponse(BaseModel):
    id: int
    ticket_id: int
    sender_id: int
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)