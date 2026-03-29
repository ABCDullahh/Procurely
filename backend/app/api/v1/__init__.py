"""V1 API router init."""

from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.auth import router as auth_router
from app.api.v1.copilot import router as copilot_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.procurement_chat import router as procurement_chat_router
from app.api.v1.providers import router as providers_router
from app.api.v1.reports import router as reports_router
from app.api.v1.requests import router as requests_router
from app.api.v1.shortlists import router as shortlists_router
from app.api.v1.vendors import router as vendors_router

router = APIRouter(prefix="/v1")
router.include_router(auth_router)
router.include_router(dashboard_router)
router.include_router(requests_router)
router.include_router(vendors_router)
router.include_router(shortlists_router)
router.include_router(analytics_router)
router.include_router(reports_router)
router.include_router(copilot_router)
router.include_router(procurement_chat_router)
router.include_router(providers_router)
router.include_router(admin_router)
