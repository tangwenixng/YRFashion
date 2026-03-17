from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base


class ShopSetting(Base):
    __tablename__ = "shop_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    shop_name: Mapped[str] = mapped_column(Text(), default="")
    shop_intro: Mapped[str] = mapped_column(Text(), default="")
    contact_phone: Mapped[str] = mapped_column(Text(), default="")
    wechat_id: Mapped[str] = mapped_column(Text(), default="")
    address: Mapped[str] = mapped_column(Text(), default="")
    business_hours: Mapped[str] = mapped_column(Text(), default="")
    homepage_banner_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    draft_payload: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, default=dict, nullable=True
    )
    draft_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
