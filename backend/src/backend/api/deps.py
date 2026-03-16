from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.core.security import decode_token, extract_token_subject
from backend.db.session import get_db
from backend.models import AdminUser, MiniappUser

# 管理端登录接口使用 OAuth2PasswordBearer，便于在 OpenAPI 中声明标准 Bearer Token 鉴权。
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/auth/login")
# 小程序端使用可选 Bearer 头，便于在依赖函数内统一返回定制化的未登录错误信息。
miniapp_bearer = HTTPBearer(auto_error=False)


def get_current_admin(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> AdminUser:
    # 管理端允许兼容历史上未携带 scope 的 token，避免升级 token 结构后旧会话全部失效。
    payload = decode_token(token)
    subject = extract_token_subject(
        payload or {},
        expected_scope="admin",
        allow_unscoped=True,
    )
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    # 除了 token 有效，还要求管理员账号存在且处于 active 状态，避免停用账号继续访问后台。
    admin = db.get(AdminUser, int(subject))
    if not admin or admin.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin account is unavailable",
        )

    return admin


def get_current_miniapp_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(miniapp_bearer),
) -> MiniappUser:
    # 先兼容无 Authorization 头的情况，避免由安全组件直接抛默认异常，统一走下面的业务错误响应。
    token = credentials.credentials if credentials else ""
    payload = decode_token(token) if token else None
    subject = extract_token_subject(payload or {}, expected_scope="miniapp")
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Miniapp authentication required",
        )

    # 小程序用户没有状态过滤逻辑，只要求用户记录仍然存在。
    user = db.get(MiniappUser, int(subject))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Miniapp user is unavailable",
        )

    return user
