from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base


class MiniappUser(Base):
    __tablename__ = "miniapp_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    openid: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    unionid: Mapped[str | None] = mapped_column(String(64), nullable=True)
    nickname: Mapped[str | None] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    pending_avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    avatar_review_status: Mapped[str] = mapped_column(String(20), default="approved")
    avatar_reject_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_visit_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_visit_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    messages = relationship("Message", back_populates="miniapp_user")
