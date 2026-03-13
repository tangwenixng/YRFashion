from datetime import datetime

from pydantic import BaseModel


class MessageReplyRequest(BaseModel):
    reply_content: str


class MessageStatusRequest(BaseModel):
    status: str


class MessageResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    miniapp_user_id: int
    miniapp_user_openid: str
    miniapp_user_nickname: str | None
    content: str
    status: str
    reply_content: str | None
    reply_at: datetime | None
    read_at: datetime | None
    created_at: datetime


class MessageListResponse(BaseModel):
    items: list[MessageResponse]
