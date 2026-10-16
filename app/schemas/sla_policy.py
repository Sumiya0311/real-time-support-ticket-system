from pydantic import BaseModel, ConfigDict, Field


class SLAPolicyCreate(BaseModel):
    priority: str = Field(pattern=r"^(High|Medium|Low)$")
    first_response_minutes: int = Field(gt=0)
    resolution_minutes: int = Field(gt=0)


class SLAPolicyResponse(BaseModel):
    id: int
    priority: str
    first_response_minutes: int
    resolution_minutes: int

    model_config = ConfigDict(from_attributes=True)