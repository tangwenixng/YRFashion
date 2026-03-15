from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.api.deps import get_current_admin
from backend.db.session import get_db
from backend.models import AdminUser, Message, MiniappUser, NotificationSetting, Product
from backend.schemas.dashboard import (
    DashboardMessageTrendPoint,
    DashboardSummaryResponse,
    DashboardTopProductItem,
)

router = APIRouter(prefix="/admin/dashboard")


def build_recent_message_trend(db: Session, days: int = 7) -> list[DashboardMessageTrendPoint]:
    today = datetime.now(UTC).date()
    start_date = today - timedelta(days=days - 1)

    grouped_rows = (
        db.query(
            func.date(Message.created_at).label("created_date"),
            func.count(Message.id).label("message_count"),
        )
        .filter(Message.created_at >= start_date)
        .group_by(func.date(Message.created_at))
        .all()
    )
    grouped_map = {str(row.created_date): int(row.message_count) for row in grouped_rows}

    return [
        DashboardMessageTrendPoint(
            date=(start_date + timedelta(days=offset)).isoformat(),
            count=grouped_map.get((start_date + timedelta(days=offset)).isoformat(), 0),
        )
        for offset in range(days)
    ]


def build_top_products(db: Session, limit: int = 5) -> list[DashboardTopProductItem]:
    rows = (
        db.query(
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            func.count(Message.id).label("message_count"),
        )
        .join(Message, Message.product_id == Product.id)
        .group_by(Product.id, Product.name)
        .order_by(func.count(Message.id).desc(), Product.id.desc())
        .limit(limit)
        .all()
    )
    return [
        DashboardTopProductItem(
            product_id=int(row.product_id),
            product_name=row.product_name,
            message_count=int(row.message_count),
        )
        for row in rows
    ]


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
        recent_message_trend=build_recent_message_trend(db),
        top_products=build_top_products(db),
    )
