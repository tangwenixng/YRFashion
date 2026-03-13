from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.api.router import api_router
from backend.core.config import settings
from backend.db.session import init_data_dirs, init_db


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_data_dirs()
    init_db()
    yield


def create_app() -> FastAPI:
    init_data_dirs()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )
    app.include_router(api_router, prefix=settings.api_prefix)
    app.mount("/uploads", StaticFiles(directory=settings.resolved_upload_dir), name="uploads")

    return app


app = create_app()


def main() -> None:
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
