from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from backend.api.deps import get_current_admin
from backend.db.session import get_db
from backend.models import AdminUser, Message
from backend.schemas.message import (
    MessageBatchReadRequest,
    MessageListResponse,
    MessageReplyRequest,
    MessageResponse,
)

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


def load_message_or_404(db: Session, message_id: int) -> Message:
    message = (
        db.query(Message)
        .options(joinedload(Message.product), joinedload(Message.miniapp_user))
        .filter(Message.id == message_id)
        .first()
    )
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    return message


@router.get("", response_model=MessageListResponse)
def list_messages(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    status_filter: str | None = Query(default=None, alias="status"),
    product_id: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> MessageListResponse:
    query = db.query(Message).options(joinedload(Message.product), joinedload(Message.miniapp_user))
    if status_filter:
        query = query.filter(Message.status == status_filter)
    if product_id is not None:
        query = query.filter(Message.product_id == product_id)

    total = query.count()
    messages = (
        query.order_by(Message.created_at.desc(), Message.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return MessageListResponse(
        items=[serialize_message(message) for message in messages],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/{message_id}", response_model=MessageResponse)
def get_message_detail(
    message_id: int,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> MessageResponse:
    message = load_message_or_404(db, message_id)
    return serialize_message(message)


@router.post("/batch-read", response_model=MessageListResponse)
def batch_mark_message_read(
    payload: MessageBatchReadRequest,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> MessageListResponse:
    message_ids = [message_id for message_id in payload.ids if message_id > 0]
    if not message_ids:
        return MessageListResponse(items=[], page=1, page_size=0, total=0)

    now = datetime.now(UTC)
    messages = (
        db.query(Message)
        .options(joinedload(Message.product), joinedload(Message.miniapp_user))
        .filter(Message.id.in_(message_ids))
        .all()
    )
    for message in messages:
        if message.status == "unread":
            message.status = "read"
        message.read_at = now
        db.add(message)

    db.commit()
    refreshed_messages = (
        db.query(Message)
        .options(joinedload(Message.product), joinedload(Message.miniapp_user))
        .filter(Message.id.in_(message_ids))
        .order_by(Message.created_at.desc(), Message.id.desc())
        .all()
    )
    return MessageListResponse(
        items=[serialize_message(message) for message in refreshed_messages],
        page=1,
        page_size=len(refreshed_messages),
        total=len(refreshed_messages),
    )


@router.post("/{message_id}/read", response_model=MessageResponse)
def mark_message_read(
    message_id: int,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> MessageResponse:
    message = load_message_or_404(db, message_id)

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
    message = load_message_or_404(db, message_id)

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
    message = load_message_or_404(db, message_id)

    now = datetime.now(UTC)
    message.reply_content = payload.reply_content
    message.reply_at = now
    message.read_at = message.read_at or now
    message.status = "replied"
    db.add(message)
    db.commit()
    db.refresh(message)
    return serialize_message(message)
