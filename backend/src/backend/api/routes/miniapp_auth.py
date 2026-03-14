from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.security import create_access_token
from backend.db.session import get_db
from backend.models import MiniappUser
from backend.schemas.miniapp import (
    MiniappLoginRequest,
    MiniappLoginResponse,
    MiniappProfileResponse,
)
from backend.services.miniapp_auth import resolve_openid_from_code

router = APIRouter(prefix="/miniapp/auth")


@router.post("/login", response_model=MiniappLoginResponse)
def login(payload: MiniappLoginRequest, db: Session = Depends(get_db)) -> MiniappLoginResponse:
    openid = resolve_openid_from_code(payload.code)
    now = datetime.now(UTC)
    user = db.query(MiniappUser).filter(MiniappUser.openid == openid).first()

    if user is None:
        user = MiniappUser(
            openid=openid,
            unionid=None,
            nickname=None,
            avatar_url=None,
            first_visit_at=now,
            last_visit_at=now,
        )
        db.add(user)
    else:
        user.last_visit_at = now
        db.add(user)

    db.commit()
    db.refresh(user)

    return MiniappLoginResponse(
        access_token=create_access_token(str(user.id), scope="miniapp"),
        user=MiniappProfileResponse(
            id=user.id,
            created_at=user.created_at,
            last_visit_at=user.last_visit_at,
        ),
    )
