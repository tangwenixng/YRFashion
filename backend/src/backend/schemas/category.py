from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CategoryStatus = Literal["active", "disabled"]


class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class CategoryCreateRequest(CategoryBase):
    sort_order: int = 0
    status: CategoryStatus = "active"


class CategoryUpdateRequest(CategoryBase):
    sort_order: int | None = None
    status: CategoryStatus | None = None


class CategorySortRequest(BaseModel):
    sort_order: int


class CategoryStatusRequest(BaseModel):
    status: CategoryStatus


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sort_order: int
    status: str
    product_count: int = 0
    created_at: datetime
    updated_at: datetime


class CategoryListResponse(BaseModel):
    items: list[CategoryResponse]
