from datetime import datetime

from pydantic import BaseModel, Field


class ShopSettingResponse(BaseModel):
    shop_name: str
    shop_intro: str
    contact_intro: str
    contact_phone: str
    wechat_id: str
    address: str
    business_hours: str
    homepage_banner_urls: list[str]
    has_unpublished_changes: bool = False
    draft_updated_at: datetime | None = None
    published_at: datetime | None = None


class ShopSettingUpdateRequest(BaseModel):
    shop_name: str = ""
    shop_intro: str = ""
    contact_intro: str = ""
    contact_phone: str = ""
    wechat_id: str = ""
    address: str = ""
    business_hours: str = ""
    homepage_banner_urls: list[str] = Field(default_factory=list)
