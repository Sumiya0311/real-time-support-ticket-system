from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Literal


class AgentCreate(BaseModel):
    user_id: int = Field(gt=0)
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    availability: Literal["Online", "Offline"] = "Offline"
    max_open_tickets: int = Field(default=10, ge=1, le=100)


class AgentResponse(BaseModel):
    id: int
    user_id: int
    name: str
    email: EmailStr
    availability: str
    max_open_tickets: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class AgentAvailabilityUpdate(BaseModel):
    availability: Literal["Online", "Offline"]