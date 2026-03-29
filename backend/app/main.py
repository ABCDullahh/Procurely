"""Procurely Backend - FastAPI Application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1 import router as v1_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.security import get_password_hash
from app.models.user import User

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers and strip server header from all responses."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        # Strip server info
        if "server" in response.headers:
            del response.headers["server"]
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if settings.app_env == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response


def init_db() -> None:
    """Initialize database with tables and seed data."""
    Base.metadata.create_all(bind=engine)

    from app.core.database import SessionLocal
    from app.services.provider_seeder import seed_providers

    db = SessionLocal()
    try:
        # Only create default admin user if no users exist in the database
        existing = db.query(User).first()
        if not existing:
            admin = User(
                email=settings.default_admin_email,
                password_hash=get_password_hash(settings.default_admin_password),
                full_name="Admin User",
                role="admin",
                tier="admin",
                is_active=True,
            )
            db.add(admin)
            db.commit()
            logger.info("Default admin user created: %s", settings.default_admin_email)

        # Seed default providers
        seed_providers(db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    init_db()
    yield
    # Shutdown


_is_production = settings.app_env == "production"

app = FastAPI(
    title="Procurely API",
    description="Procurement Search Copilot Backend",
    version="0.1.0",
    lifespan=lifespan,
    # Disable interactive docs in production
    docs_url=None if _is_production else "/docs",
    redoc_url=None if _is_production else "/redoc",
    openapi_url=None if _is_production else "/openapi.json",
)

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)

# Include API routers
app.include_router(v1_router, prefix="/api")


@app.get("/health")
def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}
