"""Shared pytest fixtures and configuration."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models import (  # noqa: F401
    ApiKey,
    AuditLog,
    ProcurementRequest,
    Report,
    SearchRun,
    Shortlist,
    ShortlistItem,
    User,
    Vendor,
    VendorAsset,
    VendorFieldEvidence,
    VendorMetrics,
    VendorSource,
)

# Create in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Apply the override once
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    """Get database session."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    """Get test client."""
    return TestClient(app)


@pytest.fixture
def test_user(db):
    """Create a test user."""
    user = User(
        email="test@procurely.dev",
        password_hash=get_password_hash("testpass123"),
        full_name="Test User",
        role="member",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    user = User(
        email="admin@procurely.dev",
        password_hash=get_password_hash("admin123"),
        full_name="Admin User",
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Create auth headers for test user."""
    token = create_access_token(test_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(admin_user):
    """Create auth headers for admin user."""
    token = create_access_token(admin_user.id)
    return {"Authorization": f"Bearer {token}"}
