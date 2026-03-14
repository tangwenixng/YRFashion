from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload

from backend.db.session import get_db
from backend.models import Product, ShopSetting
from backend.schemas.miniapp import (
    MiniappContactResponse,
    MiniappHomeResponse,
    MiniappProductCardResponse,
)

router = APIRouter(prefix="/miniapp")


def get_cover_image_url(product: Product) -> str | None:
    images = sorted(
        product.images,
        key=lambda item: (0 if item.is_cover else 1, item.sort_order, item.id),
    )
    return images[0].image_url if images else None


def serialize_product_card(product: Product) -> MiniappProductCardResponse:
    return MiniappProductCardResponse(
        id=product.id,
        name=product.name,
        tags=product.tags_json or [],
        cover_image_url=get_cover_image_url(product),
    )


@router.get("/home", response_model=MiniappHomeResponse)
def get_home(db: Session = Depends(get_db)) -> MiniappHomeResponse:
    setting = db.get(ShopSetting, 1)
    products = (
        db.query(Product)
        .options(selectinload(Product.images))
        .filter(Product.status == "published")
        .order_by(Product.sort_order.asc(), Product.id.desc())
        .limit(4)
        .all()
    )

    return MiniappHomeResponse(
        shop_name=setting.shop_name,
        shop_intro=setting.shop_intro,
        homepage_banner_urls=setting.homepage_banner_json or [],
        featured_products=[serialize_product_card(product) for product in products],
    )


@router.get("/shop/contact", response_model=MiniappContactResponse)
def get_contact(db: Session = Depends(get_db)) -> MiniappContactResponse:
    setting = db.get(ShopSetting, 1)
    return MiniappContactResponse(
        shop_name=setting.shop_name,
        contact_phone=setting.contact_phone,
        wechat_id=setting.wechat_id,
        address=setting.address,
        business_hours=setting.business_hours,
    )
