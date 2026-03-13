from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.deps import get_current_admin
from backend.db.session import get_db
from backend.models import AdminUser, MiniappUser
from backend.schemas.user import MiniappUserListResponse, MiniappUserResponse

router = APIRouter(prefix="/admin/users")


@router.get("", response_model=MiniappUserListResponse)
def list_miniapp_users(
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> MiniappUserListResponse:
    users = (
        db.query(MiniappUser)
        .order_by(MiniappUser.last_visit_at.desc(), MiniappUser.id.desc())
        .all()
    )
    return MiniappUserListResponse(
        items=[
            MiniappUserResponse(
                id=user.id,
                openid=user.openid,
                unionid=user.unionid,
                nickname=user.nickname,
                avatar_url=user.avatar_url,
                first_visit_at=user.first_visit_at,
                last_visit_at=user.last_visit_at,
                created_at=user.created_at,
            )
            for user in users
        ]
    )
