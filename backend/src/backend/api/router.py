from fastapi import APIRouter

from backend.api.routes.admin_auth import router as admin_auth_router
from backend.api.routes.admin_dashboard import router as admin_dashboard_router
from backend.api.routes.admin_messages import router as admin_messages_router
from backend.api.routes.admin_products import router as admin_products_router
from backend.api.routes.admin_settings import router as admin_settings_router
from backend.api.routes.admin_users import router as admin_users_router
from backend.api.routes.health import router as health_router

api_router = APIRouter()
api_router.include_router(admin_auth_router, tags=["admin-auth"])
api_router.include_router(admin_dashboard_router, tags=["admin-dashboard"])
api_router.include_router(admin_messages_router, tags=["admin-messages"])
api_router.include_router(admin_products_router, tags=["admin-products"])
api_router.include_router(admin_settings_router, tags=["admin-settings"])
api_router.include_router(admin_users_router, tags=["admin-users"])
api_router.include_router(health_router, tags=["health"])
