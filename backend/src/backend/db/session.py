from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from backend.core.config import settings
from backend.core.security import get_password_hash
from backend.db.base import Base
from backend.models import AdminUser, NotificationSetting, ShopSetting


def create_db_engine():
    database_url = settings.resolved_database_url
    engine_kwargs = {"future": True, "pool_pre_ping": True}

    if database_url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        engine_kwargs.pop("pool_pre_ping", None)
    else:
        engine_kwargs["pool_recycle"] = 3600

    return create_engine(database_url, **engine_kwargs)


engine = create_db_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_data_dirs() -> None:
    if settings.uses_sqlite or settings.uses_local_storage:
        settings.resolved_data_dir.mkdir(parents=True, exist_ok=True)

    if settings.uses_local_storage:
        settings.resolved_upload_dir.mkdir(parents=True, exist_ok=True)


def ensure_runtime_schema() -> None:
    inspector = inspect(engine)

    if inspector.has_table("miniapp_users"):
        miniapp_user_columns = {
            column["name"] for column in inspector.get_columns("miniapp_users")
        }
        statements: list[str] = []
        if "pending_avatar_url" not in miniapp_user_columns:
            statements.append(
                "ALTER TABLE miniapp_users ADD COLUMN pending_avatar_url VARCHAR(500)"
            )
        if "avatar_review_status" not in miniapp_user_columns:
            statements.append(
                "ALTER TABLE miniapp_users ADD COLUMN avatar_review_status VARCHAR(20) "
                "DEFAULT 'approved'"
            )
        if "avatar_reject_reason" not in miniapp_user_columns:
            statements.append(
                "ALTER TABLE miniapp_users ADD COLUMN avatar_reject_reason VARCHAR(255)"
            )
        _execute_schema_statements(statements)
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE miniapp_users SET avatar_review_status = 'approved' "
                    "WHERE avatar_review_status IS NULL OR avatar_review_status = ''"
                )
            )

    if inspector.has_table("shop_settings"):
        shop_setting_columns = {column["name"] for column in inspector.get_columns("shop_settings")}
        statements = []
        if "contact_intro" not in shop_setting_columns:
            statements.append("ALTER TABLE shop_settings ADD COLUMN contact_intro TEXT DEFAULT ''")
        if "draft_payload" not in shop_setting_columns:
            statements.append("ALTER TABLE shop_settings ADD COLUMN draft_payload JSON")
        if "draft_updated_at" not in shop_setting_columns:
            statements.append("ALTER TABLE shop_settings ADD COLUMN draft_updated_at DATETIME")
        if "published_at" not in shop_setting_columns:
            statements.append("ALTER TABLE shop_settings ADD COLUMN published_at DATETIME")
        _execute_schema_statements(statements)
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE shop_settings SET published_at = CURRENT_TIMESTAMP "
                    "WHERE published_at IS NULL"
                )
            )


def _execute_schema_statements(statements: list[str]) -> None:
    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_runtime_schema()

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
        else:
            setting = db.get(ShopSetting, 1)
            if setting is not None and setting.published_at is None:
                setting.published_at = setting.updated_at
                db.add(setting)

        if db.get(NotificationSetting, 1) is None:
            db.add(NotificationSetting(id=1))

        db.commit()
