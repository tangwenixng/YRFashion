from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.api.deps import get_current_admin
from backend.db.session import get_db
from backend.models import AdminUser, Category
from backend.schemas.category import (
    CategoryCreateRequest,
    CategoryListResponse,
    CategoryResponse,
    CategorySortRequest,
    CategoryStatusRequest,
    CategoryUpdateRequest,
)

router = APIRouter(prefix="/admin/categories")


def serialize_category(category: Category) -> CategoryResponse:
    return CategoryResponse(
        id=category.id,
        name=category.name,
        sort_order=category.sort_order,
        status=category.status,
        product_count=len(category.products),
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


def get_category_or_404(db: Session, category_id: int) -> Category:
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


def ensure_category_name_available(
    db: Session,
    name: str,
    exclude_category_id: int | None = None,
) -> None:
    query = db.query(Category).filter(Category.name == name)
    if exclude_category_id is not None:
        query = query.filter(Category.id != exclude_category_id)
    if query.first() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category name exists")


@router.get("", response_model=CategoryListResponse)
def list_categories(
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> CategoryListResponse:
    categories = (
        db.query(Category)
        .order_by(Category.sort_order.asc(), Category.id.desc())
        .all()
    )
    return CategoryListResponse(items=[serialize_category(category) for category in categories])


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreateRequest,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> CategoryResponse:
    name = payload.name.strip()
    ensure_category_name_available(db, name)

    category = Category(
        name=name,
        sort_order=payload.sort_order,
        status=payload.status,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return serialize_category(category)


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    payload: CategoryUpdateRequest,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> CategoryResponse:
    category = get_category_or_404(db, category_id)
    name = payload.name.strip()
    ensure_category_name_available(db, name, exclude_category_id=category_id)

    category.name = name
    if payload.sort_order is not None:
        category.sort_order = payload.sort_order
    if payload.status is not None:
        category.status = payload.status

    db.add(category)
    db.commit()
    db.refresh(category)
    return serialize_category(category)


@router.put("/{category_id}/sort", response_model=CategoryResponse)
def update_category_sort(
    category_id: int,
    payload: CategorySortRequest,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> CategoryResponse:
    category = get_category_or_404(db, category_id)
    category.sort_order = payload.sort_order
    db.add(category)
    db.commit()
    db.refresh(category)
    return serialize_category(category)


@router.put("/{category_id}/status", response_model=CategoryResponse)
def update_category_status(
    category_id: int,
    payload: CategoryStatusRequest,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> CategoryResponse:
    category = get_category_or_404(db, category_id)
    category.status = payload.status
    db.add(category)
    db.commit()
    db.refresh(category)
    return serialize_category(category)
