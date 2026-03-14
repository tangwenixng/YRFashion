from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from backend.api.deps import get_current_admin
from backend.db.session import get_db
from backend.models import AdminUser, Message
from backend.schemas.message import MessageListResponse, MessageReplyRequest, MessageResponse

router = APIRouter(prefix="/admin/messages")


def serialize_message(message: Message) -> MessageResponse:
    return MessageResponse(
        id=message.id,
        product_id=message.product_id,
        product_name=message.product.name,
        miniapp_user_id=message.miniapp_user_id,
        miniapp_user_openid=message.miniapp_user.openid,
        miniapp_user_nickname=message.miniapp_user.nickname,
        miniapp_user_avatar_url=message.miniapp_user.avatar_url,
        content=message.content,
        status=message.status,
        reply_content=message.reply_content,
        reply_at=message.reply_at,
        read_at=message.read_at,
        created_at=message.created_at,
    )


@router.get("", response_model=MessageListResponse)
def list_messages(
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> MessageListResponse:
    query = (
        db.query(Message)
        .options(joinedload(Message.product), joinedload(Message.miniapp_user))
        .order_by(Message.created_at.desc(), Message.id.desc())
    )
    if status_filter:
        query = query.filter(Message.status == status_filter)

    messages = query.all()
    return MessageListResponse(items=[serialize_message(message) for message in messages])


@router.post("/{message_id}/read", response_model=MessageResponse)
def mark_message_read(
    message_id: int,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> MessageResponse:
    message = (
        db.query(Message)
        .options(joinedload(Message.product), joinedload(Message.miniapp_user))
        .filter(Message.id == message_id)
        .first()
    )
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    if message.status == "unread":
        message.status = "read"
    message.read_at = datetime.now(UTC)
    db.add(message)
    db.commit()
    db.refresh(message)
    return serialize_message(message)


@router.post("/{message_id}/unread", response_model=MessageResponse)
def mark_message_unread(
    message_id: int,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> MessageResponse:
    message = (
        db.query(Message)
        .options(joinedload(Message.product), joinedload(Message.miniapp_user))
        .filter(Message.id == message_id)
        .first()
    )
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    message.status = "unread"
    message.read_at = None
    db.add(message)
    db.commit()
    db.refresh(message)
    return serialize_message(message)


@router.post("/{message_id}/reply", response_model=MessageResponse)
def reply_message(
    message_id: int,
    payload: MessageReplyRequest,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> MessageResponse:
    message = (
        db.query(Message)
        .options(joinedload(Message.product), joinedload(Message.miniapp_user))
        .filter(Message.id == message_id)
        .first()
    )
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    now = datetime.now(UTC)
    message.reply_content = payload.reply_content
    message.reply_at = now
    message.read_at = message.read_at or now
    message.status = "replied"
    db.add(message)
    db.commit()
    db.refresh(message)
    return serialize_message(message)
