from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    category_name: str = Field(min_length=2, max_length=100)
    description: str | None = None


class CategoryResponse(BaseModel):
    id: int
    category_name: str
    description: str | None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)