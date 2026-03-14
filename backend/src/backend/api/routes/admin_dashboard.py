from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.deps import get_current_admin
from backend.db.session import get_db
from backend.models import AdminUser, Message, MiniappUser, NotificationSetting, Product
from backend.schemas.dashboard import DashboardSummaryResponse

router = APIRouter(prefix="/admin/dashboard")


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> DashboardSummaryResponse:
    unread_message_count = db.query(Message).filter(Message.status == "unread").count()
    product_count = db.query(Product).count()
    miniapp_user_count = db.query(MiniappUser).count()
    notification_setting = db.get(NotificationSetting, 1)
    return DashboardSummaryResponse(
        unread_message_count=unread_message_count,
        product_count=product_count,
        miniapp_user_count=miniapp_user_count,
        notification_enabled=notification_setting.enabled,
        notification_channel=notification_setting.channel if notification_setting.enabled else None,
    )
