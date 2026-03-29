"""Tests for vendor models and endpoints."""

import pytest

from app.core.security import create_access_token, get_password_hash
from app.models.procurement_request import ProcurementRequest
from app.models.search_run import SearchRun
from app.models.user import User
from app.models.vendor import Vendor
from app.models.vendor_asset import VendorAsset
from app.models.vendor_evidence import VendorFieldEvidence
from app.models.vendor_metrics import VendorMetrics
from app.models.vendor_source import VendorSource


@pytest.fixture
def test_request(db, test_user):
    """Create a test procurement request."""
    request = ProcurementRequest(
        title="Test Request",
        description="Testing vendor discovery",
        category="Software",
        keywords='["testing", "automation"]',
        created_by_user_id=test_user.id,
        status="PENDING",
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


@pytest.fixture
def test_run(db, test_request):
    """Create a test search run."""
    run = SearchRun(
        request_id=test_request.id,
        status="COMPLETED",
        vendors_found=2,
        sources_searched=5,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


@pytest.fixture
def test_vendor_with_data(db, test_run):
    """Create a vendor with full data (source, evidence, metrics, asset)."""
    vendor = Vendor(
        name="Acme Corp",
        website="https://acme.com",
        description="Leading provider of testing tools",
        location="San Francisco, CA",
        country="USA",
        industry="Software",
        founded_year=2015,
        employee_count="50-200",
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)

    # Add source
    source = VendorSource(
        vendor_id=vendor.id,
        search_run_id=test_run.id,
        source_url="https://acme.com/about",
        source_type="WEBSITE",
        page_title="About Acme",
        fetch_status="SUCCESS",
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    # Add evidence
    evidence = VendorFieldEvidence(
        vendor_id=vendor.id,
        source_id=source.id,
        field_name="description",
        field_value="Leading provider of testing tools",
        evidence_url="https://acme.com/about",
        evidence_snippet="Acme Corp is a leading provider of testing tools...",
        confidence=0.95,
        extraction_method="LLM",
    )
    db.add(evidence)

    # Add metrics
    metrics = VendorMetrics(
        vendor_id=vendor.id,
        search_run_id=test_run.id,
        fit_score=85.0,
        trust_score=78.0,
        overall_score=82.0,
        must_have_matched=3,
        must_have_total=4,
        nice_to_have_matched=2,
        nice_to_have_total=3,
        source_count=1,
        evidence_count=1,
    )
    db.add(metrics)

    # Add asset (logo)
    asset = VendorAsset(
        vendor_id=vendor.id,
        asset_type="LOGO",
        asset_url="https://acme.com/logo.png",
        source_url="https://acme.com",
        priority=1,
    )
    db.add(asset)

    db.commit()
    return vendor


class TestVendorModels:
    """Test vendor model creation."""

    def test_create_vendor(self, db):
        """Test creating a vendor."""
        vendor = Vendor(
            name="Test Vendor",
            website="https://testvendor.com",
            description="A test vendor",
        )
        db.add(vendor)
        db.commit()
        db.refresh(vendor)

        assert vendor.id is not None
        assert vendor.name == "Test Vendor"

    def test_vendor_with_relationships(self, db, test_run):
        """Test vendor with all relationships."""
        vendor = Vendor(name="Full Vendor", website="https://full.com")
        db.add(vendor)
        db.commit()

        source = VendorSource(
            vendor_id=vendor.id,
            search_run_id=test_run.id,
            source_url="https://full.com",
            source_type="WEBSITE",
            fetch_status="SUCCESS",
        )
        db.add(source)
        db.commit()

        # Verify relationship
        db.refresh(vendor)
        assert len(vendor.sources) == 1
        assert vendor.sources[0].source_url == "https://full.com"


class TestRunEndpoints:
    """Test search run endpoints."""

    def test_get_run(self, auth_headers, test_run, client):
        """Test getting a run by ID."""
        response = client.get(f"/api/v1/runs/{test_run.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_run.id
        assert data["status"] == "COMPLETED"

    def test_get_run_not_found(self, auth_headers, client):
        """Test getting a non-existent run."""
        response = client.get("/api/v1/runs/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_list_run_vendors_empty(self, auth_headers, test_run, client):
        """Test listing vendors for a run with no vendors."""
        response = client.get(f"/api/v1/runs/{test_run.id}/vendors", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["vendors"] == []
        assert data["total"] == 0

    def test_list_run_vendors_with_data(
        self, auth_headers, test_run, test_vendor_with_data, client
    ):
        """Test listing vendors for a run with vendors."""
        response = client.get(f"/api/v1/runs/{test_run.id}/vendors", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["vendors"]) == 1
        assert data["vendors"][0]["name"] == "Acme Corp"
        assert data["vendors"][0]["logo_url"] == "https://acme.com/logo.png"


class TestVendorEndpoints:
    """Test vendor endpoints."""

    def test_get_vendor(self, auth_headers, test_vendor_with_data, client):
        """Test getting a vendor by ID."""
        response = client.get(
            f"/api/v1/vendors/{test_vendor_with_data.id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Acme Corp"
        assert data["metrics"]["overall_score"] == 82.0

    def test_get_vendor_evidence(self, auth_headers, test_vendor_with_data, client):
        """Test getting vendor evidence."""
        response = client.get(
            f"/api/v1/vendors/{test_vendor_with_data.id}/evidence", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["field_name"] == "description"
        assert data[0]["evidence_url"] == "https://acme.com/about"

    def test_get_vendor_sources(self, auth_headers, test_vendor_with_data, client):
        """Test getting vendor sources."""
        response = client.get(
            f"/api/v1/vendors/{test_vendor_with_data.id}/sources", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["source_type"] == "WEBSITE"

    def test_get_vendor_assets(self, auth_headers, test_vendor_with_data, client):
        """Test getting vendor assets."""
        response = client.get(
            f"/api/v1/vendors/{test_vendor_with_data.id}/assets", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["asset_type"] == "LOGO"

    def test_vendor_access_denied_for_other_user(self, db, test_vendor_with_data, client):
        """Test that users cannot access vendors from other users' runs."""
        # Create another user
        other_user = User(
            email="other@procurely.dev",
            password_hash=get_password_hash("otherpass"),
            full_name="Other User",
            role="member",
            is_active=True,
        )
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        other_token = create_access_token(other_user.id)
        other_headers = {"Authorization": f"Bearer {other_token}"}

        response = client.get(
            f"/api/v1/vendors/{test_vendor_with_data.id}", headers=other_headers
        )
        assert response.status_code == 404  # Vendor not found for this user
