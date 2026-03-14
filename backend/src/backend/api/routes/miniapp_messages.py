from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.api.deps import get_current_miniapp_user
from backend.db.session import get_db
from backend.models import Message, MiniappUser, Product
from backend.schemas.miniapp import MiniappMessageCreateRequest, MiniappMessageCreateResponse

router = APIRouter(prefix="/miniapp/products")


@router.post("/{product_id}/messages", response_model=MiniappMessageCreateResponse, status_code=201)
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
        content=payload.content,
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
