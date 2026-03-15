from fastapi import APIRouter

from backend.api.routes.admin_accounts import router as admin_accounts_router
from backend.api.routes.admin_auth import router as admin_auth_router
from backend.api.routes.admin_categories import router as admin_categories_router
from backend.api.routes.admin_dashboard import router as admin_dashboard_router
from backend.api.routes.admin_messages import router as admin_messages_router
from backend.api.routes.admin_notifications import router as admin_notifications_router
from backend.api.routes.admin_products import router as admin_products_router
from backend.api.routes.admin_settings import router as admin_settings_router
from backend.api.routes.admin_users import router as admin_users_router
from backend.api.routes.health import router as health_router
from backend.api.routes.miniapp_auth import router as miniapp_auth_router
from backend.api.routes.miniapp_categories import router as miniapp_categories_router
from backend.api.routes.miniapp_messages import product_router as miniapp_product_messages_router
from backend.api.routes.miniapp_messages import router as miniapp_messages_router
from backend.api.routes.miniapp_products import router as miniapp_products_router
from backend.api.routes.miniapp_storefront import router as miniapp_storefront_router

api_router = APIRouter()
api_router.include_router(admin_accounts_router, tags=["admin-accounts"])
api_router.include_router(admin_auth_router, tags=["admin-auth"])
api_router.include_router(admin_categories_router, tags=["admin-categories"])
api_router.include_router(admin_dashboard_router, tags=["admin-dashboard"])
api_router.include_router(admin_messages_router, tags=["admin-messages"])
api_router.include_router(admin_notifications_router, tags=["admin-notifications"])
api_router.include_router(admin_products_router, tags=["admin-products"])
api_router.include_router(admin_settings_router, tags=["admin-settings"])
api_router.include_router(admin_users_router, tags=["admin-users"])
api_router.include_router(health_router, tags=["health"])
api_router.include_router(miniapp_auth_router, tags=["miniapp-auth"])
api_router.include_router(miniapp_categories_router, tags=["miniapp-categories"])
api_router.include_router(miniapp_messages_router, tags=["miniapp-messages"])
api_router.include_router(miniapp_product_messages_router, tags=["miniapp-product-messages"])
api_router.include_router(miniapp_products_router, tags=["miniapp-products"])
api_router.include_router(miniapp_storefront_router, tags=["miniapp-storefront"])
