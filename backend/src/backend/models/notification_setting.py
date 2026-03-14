from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base


class NotificationSetting(Base):
    __tablename__ = "notification_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    channel: Mapped[str] = mapped_column(String(20), default="wecom", server_default="wecom")
    webhook_url: Mapped[str] = mapped_column(Text(), default="", server_default="")
    message_prefix: Mapped[str] = mapped_column(
        Text(),
        default="YRFasion",
        server_default="YRFasion",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
