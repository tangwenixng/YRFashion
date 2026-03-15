from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class MiniappLoginRequest(BaseModel):
    code: str = Field(min_length=1, max_length=256)


class MiniappProfileResponse(BaseModel):
    id: int
    nickname: str | None
    avatar_url: str | None
    created_at: datetime
    last_visit_at: datetime


class MiniappLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: MiniappProfileResponse


class MiniappProfileUpdateRequest(BaseModel):
    nickname: str = Field(min_length=1, max_length=100)
    avatar_url: str = Field(min_length=1, max_length=500)

    @field_validator("nickname", "avatar_url")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Field cannot be empty")
        return normalized


class MiniappAvatarUploadResponse(BaseModel):
    avatar_url: str


class MiniappProductCardResponse(BaseModel):
    id: int
    name: str
    tags: list[str]
    cover_image_url: str | None


class MiniappCategoryResponse(BaseModel):
    id: int
    name: str
    sort_order: int


class MiniappCategoryListResponse(BaseModel):
    items: list[MiniappCategoryResponse]


class MiniappProductImageResponse(BaseModel):
    id: int
    image_url: str
    original_name: str
    sort_order: int
    is_cover: bool


class MiniappProductListResponse(BaseModel):
    items: list[MiniappProductCardResponse]
    page: int
    page_size: int
    total: int
    has_more: bool


class MiniappProductDetailResponse(BaseModel):
    id: int
    name: str
    description: str
    tags: list[str]
    cover_image_url: str | None
    images: list[MiniappProductImageResponse]
    related_products: list[MiniappProductCardResponse] = Field(default_factory=list)


class MiniappMessageCreateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=500)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Message content cannot be empty")
        return normalized


class MiniappMessageCreateResponse(BaseModel):
    id: int
    product_id: int
    miniapp_user_id: int
    content: str
    status: str
    created_at: datetime


class MiniappMessageHistoryItemResponse(BaseModel):
    id: int
    product_id: int
    content: str
    status: str
    reply_content: str | None
    reply_at: datetime | None
    created_at: datetime


class MiniappMessageHistoryResponse(BaseModel):
    items: list[MiniappMessageHistoryItemResponse]


class MiniappHomeResponse(BaseModel):
    shop_name: str
    shop_intro: str
    homepage_banner_urls: list[str]
    featured_products: list[MiniappProductCardResponse]


class MiniappContactResponse(BaseModel):
    shop_name: str
    contact_phone: str
    wechat_id: str
    address: str
    business_hours: str
