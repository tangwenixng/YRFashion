from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.deps import get_current_admin
from backend.db.session import get_db
from backend.models import AdminUser, ShopSetting
from backend.schemas.setting import ShopSettingResponse, ShopSettingUpdateRequest

router = APIRouter(prefix="/admin/settings")


def serialize_settings(setting: ShopSetting) -> ShopSettingResponse:
    return ShopSettingResponse(
        shop_name=setting.shop_name,
        shop_intro=setting.shop_intro,
        contact_phone=setting.contact_phone,
        wechat_id=setting.wechat_id,
        address=setting.address,
        business_hours=setting.business_hours,
        homepage_banner_urls=setting.homepage_banner_json or [],
    )


@router.get("", response_model=ShopSettingResponse)
def get_settings(
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> ShopSettingResponse:
    setting = db.get(ShopSetting, 1)
    return serialize_settings(setting)


@router.put("", response_model=ShopSettingResponse)
def update_settings(
    payload: ShopSettingUpdateRequest,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> ShopSettingResponse:
    setting = db.get(ShopSetting, 1)
    setting.shop_name = payload.shop_name
    setting.shop_intro = payload.shop_intro
    setting.contact_phone = payload.contact_phone
    setting.wechat_id = payload.wechat_id
    setting.address = payload.address
    setting.business_hours = payload.business_hours
    setting.homepage_banner_json = payload.homepage_banner_urls
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return serialize_settings(setting)
