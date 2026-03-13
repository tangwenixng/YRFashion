from pydantic import BaseModel, Field


class ShopSettingResponse(BaseModel):
    shop_name: str
    shop_intro: str
    contact_phone: str
    wechat_id: str
    address: str
    business_hours: str
    homepage_banner_urls: list[str]


class ShopSettingUpdateRequest(BaseModel):
    shop_name: str = ""
    shop_intro: str = ""
    contact_phone: str = ""
    wechat_id: str = ""
    address: str = ""
    business_hours: str = ""
    homepage_banner_urls: list[str] = Field(default_factory=list)
