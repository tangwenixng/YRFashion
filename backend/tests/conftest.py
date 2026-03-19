# ruff: noqa: E402

import os
import shutil
from pathlib import Path

import pytest

TEST_DATA_DIR = Path(__file__).resolve().parent / ".tmp_test_data"
os.environ["DATA_DIR"] = str(TEST_DATA_DIR)
os.environ["MINIAPP_APP_ID"] = "test-miniapp-app-id"
os.environ["MINIAPP_APP_SECRET"] = "test-miniapp-app-secret"

from backend.api.routes import miniapp_auth as miniapp_auth_routes
from backend.core.config import settings
from backend.db.base import Base
from backend.db.session import engine, init_data_dirs, init_db
from backend.services.miniapp_auth import MiniappCode2SessionResult


@pytest.fixture(autouse=True)
def reset_test_environment() -> None:
    Base.metadata.drop_all(bind=engine)

    if settings.resolved_upload_dir.exists():
        shutil.rmtree(settings.resolved_upload_dir)

    init_data_dirs()
    Base.metadata.create_all(bind=engine)
    init_db()

    yield


@pytest.fixture(autouse=True)
def mock_miniapp_code2session(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_resolve_miniapp_session_from_code(code: str) -> MiniappCode2SessionResult:
        normalized = code.strip()
        return MiniappCode2SessionResult(
            openid=f"test-openid-{normalized}",
            unionid=f"test-unionid-{normalized}",
        )

    monkeypatch.setattr(
        miniapp_auth_routes,
        "resolve_miniapp_session_from_code",
        fake_resolve_miniapp_session_from_code,
    )


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    Base.metadata.drop_all(bind=engine)
    if TEST_DATA_DIR.exists():
        shutil.rmtree(TEST_DATA_DIR, ignore_errors=True)
