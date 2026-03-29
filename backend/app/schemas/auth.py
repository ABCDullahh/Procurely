"""Authentication schemas."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Request schema for login."""

    email: EmailStr
    password: str = Field(..., min_length=6)


class TokenResponse(BaseModel):
    """Response schema with access and refresh tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Request schema for token refresh."""

    refresh_token: str


class UserResponse(BaseModel):
    """Response schema for user data."""

    id: int
    email: str
    full_name: str | None
    role: str
    tier: str = "free"
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TierInfoResponse(BaseModel):
    """Response schema for user tier and search usage info."""

    tier: str
    searches_used: int
    searches_limit: int  # -1 means unlimited
    can_search: bool


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str | None = None
    role: str = "member"


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    email: EmailStr | None = None
    full_name: str | None = None
    role: str | None = None
    is_active: bool | None = None
