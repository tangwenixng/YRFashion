from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

NotificationChannel = Literal["wecom", "feishu", "generic"]


class NotificationSettingResponse(BaseModel):
    enabled: bool
    channel: NotificationChannel
    webhook_url: str
    message_prefix: str
    updated_at: datetime


class NotificationSettingUpdateRequest(BaseModel):
    enabled: bool = False
    channel: NotificationChannel = "wecom"
    webhook_url: str = ""
    message_prefix: str = Field(default="YRFasion", max_length=100)


class NotificationSendResponse(BaseModel):
    success: bool
    message: str
