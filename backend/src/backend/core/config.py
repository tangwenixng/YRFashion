from pathlib import Path

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
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60 * 24

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
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        db_path = self.resolved_data_dir / "app.db"
        return f"sqlite:///{db_path.as_posix()}"


settings = Settings()
