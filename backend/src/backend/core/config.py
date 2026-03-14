from pathlib import Path
from urllib.parse import quote_plus

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "YRFasion Backend"
    app_version: str = "0.1.0"
    api_prefix: str = "/api"
    base_dir: Path = Path(__file__).resolve().parents[3]
    data_dir: Path | None = None
    upload_dir: Path | None = None
    database_url: str | None = None
    mysql_host: str | None = None
    mysql_port: int = 3306
    mysql_user: str | None = None
    mysql_password: str | None = None
    mysql_database: str | None = None
    mysql_charset: str = "utf8mb4"
    storage_backend: str = "local"
    storage_bucket: str | None = None
    storage_region: str | None = None
    storage_secret_id: str | None = None
    storage_secret_key: str | None = None
    storage_public_base_url: str | None = None
    storage_path_prefix: str = ""
    cors_allow_origins: str = ""
    secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    bootstrap_admin_username: str = "admin"
    bootstrap_admin_password: str = "admin123456"
    bootstrap_admin_display_name: str = "Store Admin"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @computed_field
    @property
    def resolved_data_dir(self) -> Path:
        if self.data_dir is not None:
            return self.data_dir
        return self.base_dir / "data"

    @computed_field
    @property
    def resolved_upload_dir(self) -> Path:
        if self.upload_dir is not None:
            return self.upload_dir
        return self.resolved_data_dir / "uploads"

    @computed_field
    @property
    def resolved_storage_backend(self) -> str:
        backend = self.storage_backend.strip().lower()
        if backend in {"cloudbase", "cos"}:
            return "cloudbase"
        return "local"

    @computed_field
    @property
    def resolved_storage_type(self) -> str:
        if self.resolved_storage_backend == "cloudbase":
            return "cloudbase"
        return "local"

    @computed_field
    @property
    def uses_local_storage(self) -> bool:
        return self.resolved_storage_backend == "local"

    @computed_field
    @property
    def uses_cloud_storage(self) -> bool:
        return self.resolved_storage_backend == "cloudbase"

    @computed_field
    @property
    def resolved_storage_path_prefix(self) -> str:
        return self.storage_path_prefix.strip().strip("/")

    @computed_field
    @property
    def resolved_cors_allow_origins(self) -> list[str]:
        raw = self.cors_allow_origins.strip()
        if not raw:
            return []
        return [item.strip() for item in raw.split(",") if item.strip()]

    @computed_field
    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        if (
            self.mysql_host
            and self.mysql_user
            and self.mysql_password is not None
            and self.mysql_database
        ):
            username = quote_plus(self.mysql_user)
            password = quote_plus(self.mysql_password)
            database = quote_plus(self.mysql_database)
            return (
                f"mysql+pymysql://{username}:{password}@{self.mysql_host}:{self.mysql_port}/"
                f"{database}?charset={self.mysql_charset}"
            )
        db_path = self.resolved_data_dir / "app.db"
        return f"sqlite:///{db_path.as_posix()}"

    @computed_field
    @property
    def uses_sqlite(self) -> bool:
        return self.resolved_database_url.startswith("sqlite")

    def validate_runtime_configuration(self) -> None:
        if self.uses_cloud_storage:
            required_fields = {
                "STORAGE_BUCKET": self.storage_bucket,
                "STORAGE_REGION": self.storage_region,
                "STORAGE_SECRET_ID": self.storage_secret_id,
                "STORAGE_SECRET_KEY": self.storage_secret_key,
            }
            missing = [name for name, value in required_fields.items() if not value]
            if missing:
                joined = ", ".join(missing)
                raise RuntimeError(
                    "Cloud storage is enabled but required environment variables are missing: "
                    f"{joined}"
                )


settings = Settings()
