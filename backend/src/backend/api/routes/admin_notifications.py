from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.api.deps import get_current_admin
from backend.db.session import get_db
from backend.models import AdminUser, Message, NotificationSetting
from backend.schemas.notification import (
    NotificationSendResponse,
    NotificationSettingResponse,
    NotificationSettingUpdateRequest,
)
from backend.services.notification_sender import build_prefixed_text, send_webhook_message

router = APIRouter(prefix="/admin/notifications")


def get_notification_setting(db: Session) -> NotificationSetting:
    return db.get(NotificationSetting, 1)


def serialize_notification_setting(setting: NotificationSetting) -> NotificationSettingResponse:
    return NotificationSettingResponse(
        enabled=setting.enabled,
        channel=setting.channel,
        webhook_url=setting.webhook_url,
        message_prefix=setting.message_prefix,
        updated_at=setting.updated_at,
    )


@router.get("/settings", response_model=NotificationSettingResponse)
def get_notification_settings(
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> NotificationSettingResponse:
    return serialize_notification_setting(get_notification_setting(db))


@router.put("/settings", response_model=NotificationSettingResponse)
def update_notification_settings(
    payload: NotificationSettingUpdateRequest,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> NotificationSettingResponse:
    if payload.enabled and not payload.webhook_url.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook URL is required when notification is enabled",
        )

    setting = get_notification_setting(db)
    setting.enabled = payload.enabled
    setting.channel = payload.channel
    setting.webhook_url = payload.webhook_url.strip()
    setting.message_prefix = payload.message_prefix.strip() or "YRFasion"
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return serialize_notification_setting(setting)


@router.post("/test", response_model=NotificationSendResponse)
def send_test_notification(
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> NotificationSendResponse:
    setting = get_notification_setting(db)
    message = build_prefixed_text(setting, "管理后台测试提醒：Webhook 通道已连通。")
    send_webhook_message(setting, message)
    return NotificationSendResponse(success=True, message="测试提醒已发送")


@router.post("/unread-summary", response_model=NotificationSendResponse)
def send_unread_summary_notification(
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> NotificationSendResponse:
    setting = get_notification_setting(db)
    unread_count = db.query(Message).filter(Message.status == "unread").count()
    message = build_prefixed_text(
        setting,
        f"当前未读留言 {unread_count} 条，请尽快进入管理后台处理。",
    )
    send_webhook_message(setting, message)
    return NotificationSendResponse(success=True, message="未读汇总提醒已发送")
