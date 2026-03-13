from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    miniapp_user_id: Mapped[int] = mapped_column(ForeignKey("miniapp_users.id"), index=True)
    content: Mapped[str] = mapped_column(Text())
    status: Mapped[str] = mapped_column(String(20), default="unread", server_default="unread")
    reply_content: Mapped[str | None] = mapped_column(Text(), nullable=True)
    reply_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    product = relationship("Product", back_populates="messages")
    miniapp_user = relationship("MiniappUser", back_populates="messages")
