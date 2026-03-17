from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from backend.api.deps import get_current_miniapp_user
from backend.db.session import get_db
from backend.models import Message, MiniappUser, Product
from backend.schemas.miniapp import (
    MiniappMessageCreateRequest,
    MiniappMessageCreateResponse,
    MiniappMessageHistoryItemResponse,
    MiniappMessageHistoryResponse,
)
from backend.services.content_safety import ensure_safe_text

router = APIRouter()


def serialize_message_history_item(message: Message) -> MiniappMessageHistoryItemResponse:
    return MiniappMessageHistoryItemResponse(
        id=message.id,
        product_id=message.product_id,
        product_name=message.product.name,
        content=message.content,
        status=message.status,
        reply_content=message.reply_content,
        reply_at=message.reply_at,
        created_at=message.created_at,
    )


@router.get("/miniapp/messages", response_model=MiniappMessageHistoryResponse)
def list_current_user_messages(
    product_id: int | None = Query(default=None, ge=1),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: MiniappUser = Depends(get_current_miniapp_user),
) -> MiniappMessageHistoryResponse:
    query = (
        db.query(Message)
        .options(joinedload(Message.product))
        .filter(Message.miniapp_user_id == current_user.id)
    )
    if product_id is not None:
        query = query.filter(Message.product_id == product_id)

    total = query.count()
    messages = (
        query.order_by(Message.created_at.desc(), Message.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return MiniappMessageHistoryResponse(
        items=[serialize_message_history_item(message) for message in messages],
        page=page,
        page_size=page_size,
        total=total,
    )


product_router = APIRouter(prefix="/miniapp/products")


@product_router.get("/{product_id}/messages", response_model=MiniappMessageHistoryResponse)
def list_product_messages(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: MiniappUser = Depends(get_current_miniapp_user),
) -> MiniappMessageHistoryResponse:
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.status == "published")
        .first()
    )
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    messages = (
        db.query(Message)
        .options(joinedload(Message.product))
        .filter(Message.product_id == product_id, Message.miniapp_user_id == current_user.id)
        .order_by(Message.created_at.desc(), Message.id.desc())
        .all()
    )

    return MiniappMessageHistoryResponse(
        items=[serialize_message_history_item(message) for message in messages],
        page=1,
        page_size=len(messages),
        total=len(messages),
    )


@product_router.post(
    "/{product_id}/messages",
    response_model=MiniappMessageCreateResponse,
    status_code=201,
)
def create_message(
    product_id: int,
    payload: MiniappMessageCreateRequest,
    db: Session = Depends(get_db),
    current_user: MiniappUser = Depends(get_current_miniapp_user),
) -> MiniappMessageCreateResponse:
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.status == "published")
        .first()
    )
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    message = Message(
        product_id=product_id,
        miniapp_user_id=current_user.id,
        content=ensure_safe_text(payload.content, field_label="留言内容"),
        status="unread",
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    return MiniappMessageCreateResponse(
        id=message.id,
        product_id=message.product_id,
        miniapp_user_id=message.miniapp_user_id,
        content=message.content,
        status=message.status,
        created_at=message.created_at,
    )
