from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.models import Category
from backend.schemas.miniapp import MiniappCategoryListResponse, MiniappCategoryResponse

router = APIRouter(prefix="/miniapp/categories")


@router.get("", response_model=MiniappCategoryListResponse)
def list_categories(db: Session = Depends(get_db)) -> MiniappCategoryListResponse:
    categories = (
        db.query(Category)
        .filter(Category.status == "active")
        .order_by(Category.sort_order.asc(), Category.id.desc())
        .all()
    )
    return MiniappCategoryListResponse(
        items=[
            MiniappCategoryResponse(
                id=category.id,
                name=category.name,
                sort_order=category.sort_order,
            )
            for category in categories
        ]
    )
