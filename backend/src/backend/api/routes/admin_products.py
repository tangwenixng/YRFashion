from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session, selectinload

from backend.api.deps import get_current_admin
from backend.db.session import get_db
from backend.models import AdminUser, Category, Product, ProductImage
from backend.schemas.product import (
    ProductCreateRequest,
    ProductImageResponse,
    ProductImageSortRequest,
    ProductListResponse,
    ProductResponse,
    ProductSortRequest,
    ProductUpdateRequest,
)
from backend.services.local_storage import delete_local_file, save_product_image

router = APIRouter(prefix="/admin/products")


def serialize_product(product: Product) -> ProductResponse:
    return ProductResponse(
        id=product.id,
        name=product.name,
        category_id=product.category_id,
        category_name=product.category.name if product.category else None,
        description=product.description,
        tags=product.tags_json or [],
        status=product.status,
        sort_order=product.sort_order,
        created_at=product.created_at,
        updated_at=product.updated_at,
        images=[
            ProductImageResponse.model_validate(image)
            for image in sorted(product.images, key=lambda item: (item.sort_order, item.id))
        ],
    )


def validate_category(db: Session, category_id: int | None) -> None:
    if category_id is None:
        return
    if db.get(Category, category_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found")


def load_product_with_relations(db: Session, product_id: int) -> Product | None:
    return (
        db.query(Product)
        .options(selectinload(Product.images), selectinload(Product.category))
        .filter(Product.id == product_id)
        .first()
    )


def get_product_or_404(db: Session, product_id: int) -> Product:
    product = load_product_with_relations(db, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


def assign_cover_from_images(images: list[ProductImage]) -> None:
    if not images:
        return
    next_cover = sorted(images, key=lambda item: (item.sort_order, item.id))[0]
    for image in images:
        image.is_cover = image.id == next_cover.id


def get_product_image_or_404(product: Product, image_id: int) -> ProductImage:
    image = next((item for item in product.images if item.id == image_id), None)
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product image not found")
    return image


@router.get("", response_model=ProductListResponse)
def list_products(
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> ProductListResponse:
    products = (
        db.query(Product)
        .options(selectinload(Product.images), selectinload(Product.category))
        .order_by(Product.sort_order.asc(), Product.id.desc())
        .all()
    )
    return ProductListResponse(items=[serialize_product(product) for product in products])


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreateRequest,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> ProductResponse:
    validate_category(db, payload.category_id)
    product = Product(
        name=payload.name,
        category_id=payload.category_id,
        description=payload.description,
        tags_json=payload.tags,
        status=payload.status,
        sort_order=payload.sort_order,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return serialize_product(product)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> ProductResponse:
    return serialize_product(get_product_or_404(db, product_id))


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    payload: ProductUpdateRequest,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> ProductResponse:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    validate_category(db, payload.category_id)
    product.name = payload.name
    product.category_id = payload.category_id
    product.description = payload.description
    product.tags_json = payload.tags
    product.status = payload.status
    if payload.sort_order is not None:
        product.sort_order = payload.sort_order

    db.add(product)
    db.commit()
    db.refresh(product)
    return get_product(product_id=product_id, db=db)


@router.put("/{product_id}/sort", response_model=ProductResponse)
def update_product_sort(
    product_id: int,
    payload: ProductSortRequest,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> ProductResponse:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    product.sort_order = payload.sort_order
    db.add(product)
    db.commit()
    return get_product(product_id=product_id, db=db)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> None:
    product = get_product_or_404(db, product_id)
    storage_paths = [
        image.storage_path for image in product.images if image.storage_type == "local"
    ]

    db.delete(product)
    db.commit()

    for storage_path in storage_paths:
        delete_local_file(storage_path)


@router.post("/{product_id}/images", response_model=ProductImageResponse)
def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    sort_order: int = Form(0),
    is_cover: bool = Form(False),
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> ProductImageResponse:
    product = get_product_or_404(db, product_id)

    storage_path, image_url = save_product_image(product_id, file)

    if is_cover:
        for image in product.images:
            image.is_cover = False

    image = ProductImage(
        product_id=product_id,
        storage_type="local",
        storage_path=storage_path,
        image_url=image_url,
        original_name=Path(file.filename or "").name or "upload",
        sort_order=sort_order,
        is_cover=is_cover or len(product.images) == 0,
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return ProductImageResponse.model_validate(image)


@router.put("/{product_id}/images/sort", response_model=ProductResponse)
def update_product_images_sort(
    product_id: int,
    payload: ProductImageSortRequest,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> ProductResponse:
    product = get_product_or_404(db, product_id)
    image_map = {image.id: image for image in product.images}

    if len(payload.items) != len(image_map):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image sort payload does not match product images",
        )

    for item in payload.items:
        image = image_map.get(item.id)
        if image is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image sort payload contains invalid image id",
            )
        image.sort_order = item.sort_order
        db.add(image)

    if not any(image.is_cover for image in image_map.values()):
        assign_cover_from_images(list(image_map.values()))

    db.commit()
    return get_product(product_id=product_id, db=db)


@router.post("/{product_id}/images/{image_id}/cover", response_model=ProductResponse)
def set_product_image_cover(
    product_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> ProductResponse:
    product = get_product_or_404(db, product_id)
    target_image = get_product_image_or_404(product, image_id)

    for image in product.images:
        image.is_cover = image.id == target_image.id
        db.add(image)

    db.commit()
    return get_product(product_id=product_id, db=db)


@router.delete("/{product_id}/images/{image_id}", response_model=ProductResponse)
def delete_product_image(
    product_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> ProductResponse:
    product = get_product_or_404(db, product_id)
    image = get_product_image_or_404(product, image_id)
    was_cover = image.is_cover
    storage_path = image.storage_path

    db.delete(image)
    db.flush()

    remaining_images = [item for item in product.images if item.id != image_id]
    if was_cover:
        assign_cover_from_images(remaining_images)
        for item in remaining_images:
            db.add(item)

    db.commit()
    delete_local_file(storage_path)
    return get_product(product_id=product_id, db=db)
