# ruff: noqa: E402

import os
import shutil
from pathlib import Path

import pytest

TEST_DATA_DIR = Path(__file__).resolve().parent / ".tmp_test_data"
os.environ["DATA_DIR"] = str(TEST_DATA_DIR)

from backend.core.config import settings
from backend.db.base import Base
from backend.db.session import engine, init_data_dirs, init_db


@pytest.fixture(autouse=True)
def reset_test_environment() -> None:
    Base.metadata.drop_all(bind=engine)

    if settings.resolved_upload_dir.exists():
        shutil.rmtree(settings.resolved_upload_dir)

    init_data_dirs()
    Base.metadata.create_all(bind=engine)
    init_db()

    yield


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    Base.metadata.drop_all(bind=engine)
    if TEST_DATA_DIR.exists():
        shutil.rmtree(TEST_DATA_DIR, ignore_errors=True)
