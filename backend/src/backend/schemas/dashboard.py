from pydantic import BaseModel


class DashboardMessageTrendPoint(BaseModel):
    date: str
    count: int


class DashboardTopProductItem(BaseModel):
    product_id: int
    product_name: str
    message_count: int


class DashboardSummaryResponse(BaseModel):
    unread_message_count: int
    product_count: int
    miniapp_user_count: int
    notification_enabled: bool
    notification_channel: str | None
    recent_message_trend: list[DashboardMessageTrendPoint]
    top_products: list[DashboardTopProductItem]
