from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.core.config import settings
from backend.core.security import get_password_hash
from backend.db.base import Base
from backend.models import AdminUser, ShopSetting

engine = create_engine(settings.resolved_database_url, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_data_dirs() -> None:
    settings.resolved_data_dir.mkdir(parents=True, exist_ok=True)
    settings.resolved_upload_dir.mkdir(parents=True, exist_ok=True)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        admin = (
            db.query(AdminUser)
            .filter(AdminUser.username == settings.bootstrap_admin_username)
            .first()
        )
        if admin is None:
            db.add(
                AdminUser(
                    username=settings.bootstrap_admin_username,
                    password_hash=get_password_hash(settings.bootstrap_admin_password),
                    display_name=settings.bootstrap_admin_display_name,
                )
            )

        if db.get(ShopSetting, 1) is None:
            db.add(ShopSetting(id=1))

        db.commit()
