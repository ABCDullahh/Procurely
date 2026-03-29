"""Tests for analytics and reports API endpoints."""

import json

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models import (
    ProcurementRequest,
    Report,
    SearchRun,
    User,
    Vendor,
    VendorMetrics,
    VendorSource,
)


@pytest.fixture
def client():
    """Get test client."""
    return TestClient(app)


class TestAnalyticsEndpoint:
    """Tests for GET /runs/{run_id}/analytics."""

    @pytest.fixture
    def run_with_vendors(self, db, test_user):
        """Create a run with vendors and metrics for analytics testing."""
        # Create request
        request = ProcurementRequest(
            title="Analytics Test Request",
            category="Software",
            keywords=json.dumps(["test", "analytics"]),
            created_by_user_id=test_user.id,
        )
        db.add(request)
        db.commit()
        db.refresh(request)

        # Create run
        run = SearchRun(
            request_id=request.id,
            status="COMPLETED",
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        # Create vendors
        vendors = []
        locations = ["New York", "San Francisco", "New York", "London", "Berlin"]
        industries = ["SaaS", "SaaS", "Enterprise", "SaaS", "Enterprise"]
        scores = [85, 72, 90, 65, 45]

        for i, (loc, ind, score) in enumerate(zip(locations, industries, scores)):
            vendor = Vendor(
                name=f"Vendor {i+1}",
                website=f"https://vendor{i+1}.com",
                location=loc,
                industry=ind,
            )
            db.add(vendor)
            db.commit()
            db.refresh(vendor)
            vendors.append(vendor)

            # Add source
            source = VendorSource(
                vendor_id=vendor.id,
                search_run_id=run.id,
                source_url=f"https://source{i+1}.com",
                source_type="WEB",
            )
            db.add(source)

            # Add metrics
            metrics = VendorMetrics(
                vendor_id=vendor.id,
                search_run_id=run.id,
                overall_score=float(score),
                fit_score=float(score - 5),
                trust_score=float(score + 5),
            )
            db.add(metrics)

        db.commit()

        return {"run": run, "request": request, "vendors": vendors}

    def test_analytics_returns_structure(
        self, client: TestClient, auth_headers: dict, run_with_vendors
    ):
        """Test analytics returns expected structure."""
        run_id = run_with_vendors["run"].id

        response = client.get(
            f"/api/v1/runs/{run_id}/analytics",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert "run_summary" in data
        assert "totals" in data
        assert "distributions" in data
        assert "top_vendors" in data

        # Check totals
        assert data["totals"]["vendors_count"] == 5
        assert data["totals"]["sources_count"] == 5

        # Check distributions have expected keys
        assert "vendors_by_location" in data["distributions"]
        assert "vendors_by_industry" in data["distributions"]
        assert "score_distribution" in data["distributions"]
        assert "average_scores" in data["distributions"]

        # Check top vendors (should be sorted by score desc)
        assert len(data["top_vendors"]) == 5
        assert data["top_vendors"][0]["overall_score"] == 90  # Highest score

    def test_analytics_location_distribution(
        self, client: TestClient, auth_headers: dict, run_with_vendors
    ):
        """Test location distribution is correct."""
        run_id = run_with_vendors["run"].id

        response = client.get(
            f"/api/v1/runs/{run_id}/analytics",
            headers=auth_headers,
        )
        data = response.json()

        locations = data["distributions"]["vendors_by_location"]
        # New York appears 2 times
        ny_loc = next((loc for loc in locations if loc["location"] == "New York"), None)
        assert ny_loc is not None
        assert ny_loc["count"] == 2

    def test_analytics_rbac_denied(
        self, client: TestClient, auth_headers: dict, db, run_with_vendors
    ):
        """Test user cannot access another user's run analytics."""
        # Create another user
        other_user = User(
            email="other@example.com",
            password_hash=get_password_hash("password"),
            full_name="Other User",
        )
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        # Create another request owned by other user
        other_request = ProcurementRequest(
            title="Other Request",
            category="Other",
            keywords=json.dumps(["other"]),
            created_by_user_id=other_user.id,
        )
        db.add(other_request)
        db.commit()

        # Create run for other user
        other_run = SearchRun(
            request_id=other_request.id,
            status="COMPLETED",
        )
        db.add(other_run)
        db.commit()
        db.refresh(other_run)

        # Try to access as test_user
        response = client.get(
            f"/api/v1/runs/{other_run.id}/analytics",
            headers=auth_headers,
        )
        assert response.status_code == 403


class TestReportsEndpoint:
    """Tests for reports CRUD and export."""

    @pytest.fixture
    def completed_run(self, db, test_user):
        """Create a completed run for export testing."""
        request = ProcurementRequest(
            title="Export Test Request",
            category="Software",
            keywords=json.dumps(["export"]),
            must_have_criteria=json.dumps(["API"]),
            nice_to_have_criteria=json.dumps(["Support"]),
            created_by_user_id=test_user.id,
        )
        db.add(request)
        db.commit()
        db.refresh(request)

        run = SearchRun(
            request_id=request.id,
            status="COMPLETED",
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        return {"run": run, "request": request}

    def test_export_creates_report(
        self, client: TestClient, auth_headers: dict, db, completed_run
    ):
        """Test export creates a report with HTML content."""
        run_id = completed_run["run"].id

        response = client.post(
            f"/api/v1/runs/{run_id}/export",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["id"] is not None
        assert data["run_id"] == run_id
        assert data["format"] == "HTML"
        assert data["status"] == "COMPLETED"

        # Verify report saved in DB
        report = db.query(Report).filter(Report.id == data["id"]).first()
        assert report is not None
        assert report.html_content is not None
        assert len(report.html_content) > 100
        assert "Export Test Request" in report.html_content

    def test_list_reports_returns_user_reports(
        self, client: TestClient, auth_headers: dict, db, completed_run
    ):
        """Test list reports returns only current user's reports."""
        run_id = completed_run["run"].id

        # Create a report first
        client.post(f"/api/v1/runs/{run_id}/export", headers=auth_headers)

        response = client.get("/api/v1/reports", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["total"] >= 1
        assert len(data["reports"]) >= 1
        assert data["reports"][0]["run_id"] == run_id

    def test_get_report_returns_html_content(
        self, client: TestClient, auth_headers: dict, completed_run
    ):
        """Test get report returns HTML content."""
        run_id = completed_run["run"].id

        # Create report
        export_resp = client.post(
            f"/api/v1/runs/{run_id}/export",
            headers=auth_headers,
        )
        report_id = export_resp.json()["id"]

        # Get report
        response = client.get(
            f"/api/v1/reports/{report_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["html_content"] is not None
        assert "<!DOCTYPE html>" in data["html_content"]

    def test_report_rbac_denied(
        self, client: TestClient, auth_headers: dict, db, completed_run
    ):
        """Test user cannot access another user's report."""
        # Create report as test_user
        run_id = completed_run["run"].id
        export_resp = client.post(
            f"/api/v1/runs/{run_id}/export",
            headers=auth_headers,
        )
        report_id = export_resp.json()["id"]

        # Create another user
        other_user = User(
            email="reporter@example.com",
            password_hash=get_password_hash("password"),
            full_name="Reporter User",
        )
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        # Create token directly
        other_token = create_access_token(other_user.id)
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # Try to access report as other user
        response = client.get(
            f"/api/v1/reports/{report_id}",
            headers=other_headers,
        )
        assert response.status_code == 403
