from backend.models import Product, ProductImage
from backend.schemas.miniapp import (
    MiniappProductCardResponse,
    MiniappProductDetailResponse,
    MiniappProductImageResponse,
)


def sort_product_images(images: list[ProductImage]) -> list[ProductImage]:
    return sorted(
        images,
        key=lambda item: (0 if item.is_cover else 1, item.sort_order, item.id),
    )


def get_cover_image_url(product: Product) -> str | None:
    images = sort_product_images(list(product.images))
    return images[0].image_url if images else None


def serialize_product_card(product: Product) -> MiniappProductCardResponse:
    return MiniappProductCardResponse(
        id=product.id,
        name=product.name,
        tags=product.tags_json or [],
        cover_image_url=get_cover_image_url(product),
    )


def serialize_product_detail(product: Product) -> MiniappProductDetailResponse:
    images = sort_product_images(list(product.images))
    return MiniappProductDetailResponse(
        id=product.id,
        name=product.name,
        description=product.description,
        tags=product.tags_json or [],
        cover_image_url=images[0].image_url if images else None,
        images=[
            MiniappProductImageResponse(
                id=image.id,
                image_url=image.image_url,
                original_name=image.original_name,
                sort_order=image.sort_order,
                is_cover=image.is_cover,
            )
            for image in images
        ],
    )
