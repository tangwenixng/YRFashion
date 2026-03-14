from pydantic import BaseModel


class DashboardSummaryResponse(BaseModel):
    unread_message_count: int
    product_count: int
    miniapp_user_count: int
    notification_enabled: bool
    notification_channel: str | None
