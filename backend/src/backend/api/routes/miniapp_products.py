from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload

from backend.db.session import get_db
from backend.models import Product
from backend.schemas.miniapp import MiniappProductDetailResponse, MiniappProductListResponse
from backend.services.miniapp_catalog import serialize_product_card, serialize_product_detail

router = APIRouter(prefix="/miniapp/products")


@router.get("", response_model=MiniappProductListResponse)
def list_products(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=20),
    db: Session = Depends(get_db),
) -> MiniappProductListResponse:
    query = (
        db.query(Product)
        .options(selectinload(Product.images))
        .filter(Product.status == "published")
    )
    total = query.count()
    items = (
        query.order_by(Product.sort_order.asc(), Product.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return MiniappProductListResponse(
        items=[serialize_product_card(product) for product in items],
        page=page,
        page_size=page_size,
        total=total,
        has_more=page * page_size < total,
    )


@router.get("/{product_id}", response_model=MiniappProductDetailResponse)
def get_product_detail(
    product_id: int,
    db: Session = Depends(get_db),
) -> MiniappProductDetailResponse:
    product = (
        db.query(Product)
        .options(selectinload(Product.images))
        .filter(Product.id == product_id, Product.status == "published")
        .first()
    )
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return serialize_product_detail(product)
