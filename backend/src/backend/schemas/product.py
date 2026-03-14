from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ProductStatus = Literal["draft", "published", "archived"]


class ProductBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category_id: int | None = None
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    status: ProductStatus = "draft"


class ProductCreateRequest(ProductBase):
    sort_order: int = 0


class ProductUpdateRequest(ProductBase):
    sort_order: int | None = None


class ProductSortRequest(BaseModel):
    sort_order: int


class ProductImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_url: str
    original_name: str
    sort_order: int
    is_cover: bool
    created_at: datetime


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category_id: int | None
    category_name: str | None
    description: str
    tags: list[str]
    status: str
    sort_order: int
    created_at: datetime
    updated_at: datetime
    images: list[ProductImageResponse]


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
