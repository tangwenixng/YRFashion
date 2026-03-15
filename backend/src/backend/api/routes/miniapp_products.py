from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import String, cast, or_
from sqlalchemy.orm import Session, selectinload

from backend.db.session import get_db
from backend.models import Category, Product
from backend.schemas.miniapp import MiniappProductDetailResponse, MiniappProductListResponse
from backend.services.miniapp_catalog import (
    get_cover_image_url,
    serialize_product_card,
    serialize_product_detail_with_related,
)

router = APIRouter(prefix="/miniapp/products")


def pick_related_products(db: Session, product: Product, limit: int = 6) -> list[Product]:
    base_tags = set(product.tags_json or [])
    candidates = (
        db.query(Product)
        .options(selectinload(Product.images))
        .filter(Product.status == "published", Product.id != product.id)
        .all()
    )

    def sort_key(item: Product) -> tuple[int, int, int, int, int]:
        item_tags = set(item.tags_json or [])
        shared_tags = len(base_tags & item_tags)
        same_category = product.category_id is not None and item.category_id == product.category_id
        has_cover = get_cover_image_url(item) is not None
        return (
            0 if same_category else 1,
            -shared_tags,
            0 if has_cover else 1,
            item.sort_order,
            -item.id,
        )

    return sorted(candidates, key=sort_key)[:limit]


@router.get("", response_model=MiniappProductListResponse)
def list_products(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=20),
    category_id: int | None = Query(default=None, ge=1),
    keyword: str | None = Query(default=None, min_length=1, max_length=100),
    db: Session = Depends(get_db),
) -> MiniappProductListResponse:
    query = (
        db.query(Product)
        .options(selectinload(Product.images))
        .filter(Product.status == "published")
    )
    if category_id is not None:
        category = (
            db.query(Category)
            .filter(Category.id == category_id, Category.status == "active")
            .first()
        )
        if category is None:
            return MiniappProductListResponse(
                items=[],
                page=page,
                page_size=page_size,
                total=0,
                has_more=False,
            )
        query = query.filter(Product.category_id == category_id)
    if keyword is not None and keyword.strip():
        normalized_keyword = f"%{keyword.strip()}%"
        query = query.filter(
            or_(
                Product.name.ilike(normalized_keyword),
                Product.description.ilike(normalized_keyword),
                cast(Product.tags_json, String).ilike(normalized_keyword),
            )
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
    return serialize_product_detail_with_related(product, pick_related_products(db, product))
