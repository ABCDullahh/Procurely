"""Admin API router - combines all admin endpoints."""

from fastapi import APIRouter

from app.api.v1.admin.api_keys import router as api_keys_router
from app.api.v1.admin.audit_logs import router as audit_logs_router
from app.api.v1.admin.settings import router as settings_router

router = APIRouter(prefix="/admin", tags=["admin"])

router.include_router(api_keys_router)
router.include_router(audit_logs_router)
router.include_router(settings_router)
