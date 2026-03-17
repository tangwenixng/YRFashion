from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.deps import get_current_admin
from backend.db.session import get_db
from backend.models import AdminUser, ShopSetting
from backend.schemas.setting import ShopSettingResponse, ShopSettingUpdateRequest
from backend.services.content_safety import ensure_compliant_storefront_text

router = APIRouter(prefix="/admin/settings")


def build_settings_payload(setting: ShopSetting) -> dict[str, str | list[str]]:
    draft_payload = setting.draft_payload or {}
    if draft_payload:
        return {
            "shop_name": str(draft_payload.get("shop_name", setting.shop_name or "")),
            "shop_intro": str(draft_payload.get("shop_intro", setting.shop_intro or "")),
            "contact_phone": str(draft_payload.get("contact_phone", setting.contact_phone or "")),
            "wechat_id": str(draft_payload.get("wechat_id", setting.wechat_id or "")),
            "address": str(draft_payload.get("address", setting.address or "")),
            "business_hours": str(
                draft_payload.get("business_hours", setting.business_hours or "")
            ),
            "homepage_banner_urls": list(
                draft_payload.get("homepage_banner_urls", setting.homepage_banner_json or [])
            ),
        }

    return {
        "shop_name": setting.shop_name,
        "shop_intro": setting.shop_intro,
        "contact_phone": setting.contact_phone,
        "wechat_id": setting.wechat_id,
        "address": setting.address,
        "business_hours": setting.business_hours,
        "homepage_banner_urls": setting.homepage_banner_json or [],
    }


def serialize_settings(setting: ShopSetting) -> ShopSettingResponse:
    payload = build_settings_payload(setting)
    return ShopSettingResponse(
        shop_name=str(payload["shop_name"]),
        shop_intro=str(payload["shop_intro"]),
        contact_phone=str(payload["contact_phone"]),
        wechat_id=str(payload["wechat_id"]),
        address=str(payload["address"]),
        business_hours=str(payload["business_hours"]),
        homepage_banner_urls=list(payload["homepage_banner_urls"]),
        has_unpublished_changes=bool(setting.draft_payload),
        draft_updated_at=setting.draft_updated_at,
        published_at=setting.published_at,
    )


def normalize_settings_payload(payload: ShopSettingUpdateRequest) -> dict[str, str | list[str]]:
    return {
        "shop_name": payload.shop_name.strip(),
        "shop_intro": ensure_compliant_storefront_text(
            payload.shop_intro, field_label="店铺介绍"
        ),
        "contact_phone": ensure_compliant_storefront_text(
            payload.contact_phone, field_label="联系电话"
        ),
        "wechat_id": payload.wechat_id.strip(),
        "address": ensure_compliant_storefront_text(payload.address, field_label="门店地址"),
        "business_hours": ensure_compliant_storefront_text(
            payload.business_hours, field_label="营业时间"
        ),
        "homepage_banner_urls": [
            item.strip() for item in payload.homepage_banner_urls if item.strip()
        ],
    }


def build_live_payload(setting: ShopSetting) -> dict[str, str | list[str]]:
    return {
        "shop_name": setting.shop_name or "",
        "shop_intro": setting.shop_intro or "",
        "contact_phone": setting.contact_phone or "",
        "wechat_id": setting.wechat_id or "",
        "address": setting.address or "",
        "business_hours": setting.business_hours or "",
        "homepage_banner_urls": setting.homepage_banner_json or [],
    }


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
    normalized_payload = normalize_settings_payload(payload)

    if normalized_payload == build_live_payload(setting):
        setting.draft_payload = {}
        setting.draft_updated_at = None
    else:
        setting.draft_payload = normalized_payload
        setting.draft_updated_at = datetime.now(UTC)

    db.add(setting)
    db.commit()
    db.refresh(setting)
    return serialize_settings(setting)


@router.post("/publish", response_model=ShopSettingResponse)
def publish_settings(
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> ShopSettingResponse:
    setting = db.get(ShopSetting, 1)
    draft_payload = setting.draft_payload or {}
    if draft_payload:
        setting.shop_name = str(draft_payload.get("shop_name", ""))
        setting.shop_intro = str(draft_payload.get("shop_intro", ""))
        setting.contact_phone = str(draft_payload.get("contact_phone", ""))
        setting.wechat_id = str(draft_payload.get("wechat_id", ""))
        setting.address = str(draft_payload.get("address", ""))
        setting.business_hours = str(draft_payload.get("business_hours", ""))
        setting.homepage_banner_json = list(draft_payload.get("homepage_banner_urls", []))
        setting.draft_payload = {}
        setting.draft_updated_at = None

    setting.published_at = datetime.now(UTC)
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return serialize_settings(setting)
