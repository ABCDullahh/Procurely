"""Authentication API endpoints."""

import logging
import time
from collections import defaultdict

from fastapi import APIRouter, HTTPException, Request, status

from app.api.deps import CurrentUser, DbSession
from app.core.security import (
    TOKEN_TYPE_REFRESH,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models.procurement_request import ProcurementRequest
from app.models.search_run import SearchRun
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    TierInfoResponse,
    TokenResponse,
    UserResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# --- Rate limiting (in-memory, single instance) ---
_login_attempts: dict[str, list[float]] = defaultdict(list)
MAX_ATTEMPTS = 5
WINDOW = 60  # seconds


def check_rate_limit(ip: str) -> None:
    """Reject if more than MAX_ATTEMPTS login requests from this IP within WINDOW seconds."""
    now = time.time()
    _login_attempts[ip] = [t for t in _login_attempts[ip] if now - t < WINDOW]
    if len(_login_attempts[ip]) >= MAX_ATTEMPTS:
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts. Try again later.",
        )
    _login_attempts[ip].append(now)


# --- Refresh-token replay protection (in-memory, single instance) ---
# NOTE: This is an in-memory set and will be cleared on restart.
# For multi-instance deployments, use Redis or a database table instead.
_used_refresh_tokens: set[str] = set()


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request, db: DbSession) -> TokenResponse:
    """Authenticate user and return tokens."""
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(client_ip)

    user = db.query(User).filter(User.email == body.email).first()

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(request: RefreshTokenRequest, db: DbSession) -> TokenResponse:
    """Refresh access token using refresh token.

    Each refresh token can only be used once (replay protection).
    """
    # Check if this refresh token has already been used
    if request.refresh_token in _used_refresh_tokens:
        logger.warning("Attempted reuse of refresh token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has already been used",
        )

    payload = decode_token(request.refresh_token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    token_type = payload.get("type")
    if token_type != TOKEN_TYPE_REFRESH:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Mark the old refresh token as used so it cannot be replayed
    _used_refresh_tokens.add(request.refresh_token)

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: CurrentUser) -> User:
    """Get current authenticated user info."""
    return current_user


@router.get("/me/tier-info", response_model=TierInfoResponse)
def get_tier_info(current_user: CurrentUser, db: DbSession) -> TierInfoResponse:
    """Get current user's tier information and search usage."""
    tier = getattr(current_user, 'tier', 'free')

    # Admin and paid users have unlimited searches
    if current_user.role == "admin" or tier in ("admin", "paid"):
        return TierInfoResponse(
            tier=tier,
            searches_used=0,
            searches_limit=-1,  # unlimited
            can_search=True,
        )

    # Free tier: count searches
    search_count = db.query(SearchRun).join(ProcurementRequest).filter(
        ProcurementRequest.created_by_user_id == current_user.id,
        SearchRun.status.in_(["COMPLETED", "RUNNING", "PENDING", "QUEUED"])
    ).count()

    return TierInfoResponse(
        tier=tier,
        searches_used=search_count,
        searches_limit=1,
        can_search=search_count < 1,
    )
