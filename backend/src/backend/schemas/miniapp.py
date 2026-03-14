from datetime import datetime

from pydantic import BaseModel, Field


class MiniappLoginRequest(BaseModel):
    code: str = Field(min_length=1, max_length=256)


class MiniappProfileResponse(BaseModel):
    id: int
    created_at: datetime
    last_visit_at: datetime


class MiniappLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: MiniappProfileResponse


class MiniappProductCardResponse(BaseModel):
    id: int
    name: str
    tags: list[str]
    cover_image_url: str | None


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
