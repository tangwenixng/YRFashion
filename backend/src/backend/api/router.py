from fastapi import APIRouter

from backend.api.routes.admin_auth import router as admin_auth_router
from backend.api.routes.health import router as health_router

api_router = APIRouter()
api_router.include_router(admin_auth_router, tags=["admin-auth"])
api_router.include_router(health_router, tags=["health"])
