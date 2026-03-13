from pydantic import BaseModel


class DashboardSummaryResponse(BaseModel):
    unread_message_count: int
    product_count: int
    miniapp_user_count: int
