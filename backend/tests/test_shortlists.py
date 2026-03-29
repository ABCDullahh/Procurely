"""Tests for Shortlist API endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestShortlistEndpoints:
    """Tests for shortlist CRUD operations."""

    def test_create_shortlist(self, client: TestClient, auth_headers: dict):
        """Test creating a shortlist."""
        response = client.post(
            "/api/v1/shortlists",
            json={"name": "My Vendor Shortlist"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My Vendor Shortlist"
        assert data["item_count"] == 0
        assert "id" in data

    def test_list_shortlists(self, client: TestClient, auth_headers: dict):
        """Test listing user's shortlists."""
        # Create a shortlist first
        client.post(
            "/api/v1/shortlists",
            json={"name": "Test List"},
            headers=auth_headers,
        )

        response = client.get("/api/v1/shortlists", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "shortlists" in data
        assert len(data["shortlists"]) >= 1

    def test_get_shortlist_detail(self, client: TestClient, auth_headers: dict):
        """Test getting shortlist with items."""
        # Create shortlist
        create_resp = client.post(
            "/api/v1/shortlists",
            json={"name": "Detail Test"},
            headers=auth_headers,
        )
        shortlist_id = create_resp.json()["id"]

        response = client.get(
            f"/api/v1/shortlists/{shortlist_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Detail Test"
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_rename_shortlist(self, client: TestClient, auth_headers: dict):
        """Test renaming a shortlist."""
        # Create shortlist
        create_resp = client.post(
            "/api/v1/shortlists",
            json={"name": "Original Name"},
            headers=auth_headers,
        )
        shortlist_id = create_resp.json()["id"]

        # Rename
        response = client.put(
            f"/api/v1/shortlists/{shortlist_id}",
            json={"name": "New Name"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "New Name"

    def test_delete_shortlist(self, client: TestClient, auth_headers: dict):
        """Test deleting a shortlist."""
        # Create shortlist
        create_resp = client.post(
            "/api/v1/shortlists",
            json={"name": "To Delete"},
            headers=auth_headers,
        )
        shortlist_id = create_resp.json()["id"]

        # Delete
        response = client.delete(
            f"/api/v1/shortlists/{shortlist_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        # Verify deleted
        get_resp = client.get(
            f"/api/v1/shortlists/{shortlist_id}",
            headers=auth_headers,
        )
        assert get_resp.status_code == 404


class TestShortlistVendorOperations:
    """Tests for adding/removing vendors from shortlists."""

    @pytest.fixture
    def shortlist_with_vendor(self, client: TestClient, auth_headers: dict, db, test_user):
        """Create a shortlist and vendor for testing."""
        from app.models import ProcurementRequest, SearchRun, Vendor, VendorMetrics

        # Create procurement request
        request = ProcurementRequest(
            title="Test Request",
            category="Software",
            keywords='["test"]',
            created_by_user_id=test_user.id,
        )
        db.add(request)
        db.commit()
        db.refresh(request)

        # Create search run
        search_run = SearchRun(
            request_id=request.id,
            status="COMPLETED",
        )
        db.add(search_run)
        db.commit()
        db.refresh(search_run)

        # Create vendor
        vendor = Vendor(
            name="Test Vendor",
            website="https://testvendor.com",
            description="A test vendor",
        )
        db.add(vendor)
        db.commit()
        db.refresh(vendor)

        # Add metrics
        metrics = VendorMetrics(
            vendor_id=vendor.id,
            search_run_id=search_run.id,
            overall_score=85.0,
            fit_score=80.0,
            trust_score=90.0,
            must_have_matched=3,
            must_have_total=4,
            nice_to_have_matched=2,
            nice_to_have_total=3,
            source_count=5,
            evidence_count=10,
        )
        db.add(metrics)
        db.commit()

        # Create shortlist
        create_resp = client.post(
            "/api/v1/shortlists",
            json={"name": "Vendor Test List"},
            headers=auth_headers,
        )
        shortlist_id = create_resp.json()["id"]

        return {"shortlist_id": shortlist_id, "vendor_id": vendor.id}

    def test_add_vendor_to_shortlist(
        self, client: TestClient, auth_headers: dict, shortlist_with_vendor: dict
    ):
        """Test adding a vendor to shortlist."""
        shortlist_id = shortlist_with_vendor["shortlist_id"]
        vendor_id = shortlist_with_vendor["vendor_id"]

        response = client.post(
            f"/api/v1/shortlists/{shortlist_id}/vendors/{vendor_id}",
            json={"notes": "Great vendor!"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["vendor_id"] == vendor_id
        assert data["notes"] == "Great vendor!"
        assert "vendor" in data
        assert data["vendor"]["name"] == "Test Vendor"

    def test_add_duplicate_vendor_fails(
        self, client: TestClient, auth_headers: dict, shortlist_with_vendor: dict
    ):
        """Test that adding same vendor twice fails."""
        shortlist_id = shortlist_with_vendor["shortlist_id"]
        vendor_id = shortlist_with_vendor["vendor_id"]

        # Add first time
        client.post(
            f"/api/v1/shortlists/{shortlist_id}/vendors/{vendor_id}",
            json={},
            headers=auth_headers,
        )

        # Try to add again
        response = client.post(
            f"/api/v1/shortlists/{shortlist_id}/vendors/{vendor_id}",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "already" in response.json()["detail"].lower()

    def test_remove_vendor_from_shortlist(
        self, client: TestClient, auth_headers: dict, shortlist_with_vendor: dict
    ):
        """Test removing a vendor from shortlist."""
        shortlist_id = shortlist_with_vendor["shortlist_id"]
        vendor_id = shortlist_with_vendor["vendor_id"]

        # Add vendor
        client.post(
            f"/api/v1/shortlists/{shortlist_id}/vendors/{vendor_id}",
            json={},
            headers=auth_headers,
        )

        # Remove vendor
        response = client.delete(
            f"/api/v1/shortlists/{shortlist_id}/vendors/{vendor_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        # Verify removed
        detail_resp = client.get(
            f"/api/v1/shortlists/{shortlist_id}",
            headers=auth_headers,
        )
        assert len(detail_resp.json()["items"]) == 0

    def test_update_vendor_notes(
        self, client: TestClient, auth_headers: dict, shortlist_with_vendor: dict
    ):
        """Test updating notes for a vendor in shortlist."""
        shortlist_id = shortlist_with_vendor["shortlist_id"]
        vendor_id = shortlist_with_vendor["vendor_id"]

        # Add vendor
        client.post(
            f"/api/v1/shortlists/{shortlist_id}/vendors/{vendor_id}",
            json={"notes": "Initial notes"},
            headers=auth_headers,
        )

        # Update notes
        response = client.put(
            f"/api/v1/shortlists/{shortlist_id}/vendors/{vendor_id}/notes",
            json={"notes": "Updated notes"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["notes"] == "Updated notes"


class TestShortlistReorder:
    """Tests for reordering shortlist items."""

    def test_reorder_items(self, client: TestClient, auth_headers: dict, db):
        """Test reordering items in shortlist."""
        from app.models import Vendor

        # Create vendors
        vendors = []
        for i in range(3):
            v = Vendor(name=f"Vendor {i}", website=f"https://vendor{i}.com")
            db.add(v)
            db.commit()
            db.refresh(v)
            vendors.append(v)

        # Create shortlist
        create_resp = client.post(
            "/api/v1/shortlists",
            json={"name": "Reorder Test"},
            headers=auth_headers,
        )
        shortlist_id = create_resp.json()["id"]

        # Add vendors
        item_ids = []
        for v in vendors:
            add_resp = client.post(
                f"/api/v1/shortlists/{shortlist_id}/vendors/{v.id}",
                json={},
                headers=auth_headers,
            )
            item_ids.append(add_resp.json()["id"])

        # Reorder: reverse the list
        reversed_ids = list(reversed(item_ids))
        response = client.put(
            f"/api/v1/shortlists/{shortlist_id}/reorder",
            json={"item_ids": reversed_ids},
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Check order
        detail = response.json()
        result_ids = [item["id"] for item in detail["items"]]
        assert result_ids == reversed_ids


class TestShortlistRBAC:
    """Tests for shortlist RBAC isolation."""

    def test_user_cannot_access_other_user_shortlist(
        self, client: TestClient, auth_headers: dict, db
    ):
        """Test that user cannot access another user's shortlist."""
        from app.core.security import get_password_hash
        from app.models import Shortlist, User

        # Create another user
        other_user = User(
            email="other@example.com",
            password_hash=get_password_hash("password"),
            full_name="Other User",
        )
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        # Create shortlist for other user
        other_shortlist = Shortlist(
            name="Other User's List",
            created_by_user_id=other_user.id,
        )
        db.add(other_shortlist)
        db.commit()
        db.refresh(other_shortlist)

        # Try to access as current user
        response = client.get(
            f"/api/v1/shortlists/{other_shortlist.id}",
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_user_cannot_modify_other_user_shortlist(
        self, client: TestClient, auth_headers: dict, db
    ):
        """Test that user cannot modify another user's shortlist."""
        from app.core.security import get_password_hash
        from app.models import Shortlist, User

        # Create another user
        other_user = User(
            email="other2@example.com",
            password_hash=get_password_hash("password"),
            full_name="Other User 2",
        )
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        # Create shortlist for other user
        other_shortlist = Shortlist(
            name="Other User's List 2",
            created_by_user_id=other_user.id,
        )
        db.add(other_shortlist)
        db.commit()
        db.refresh(other_shortlist)

        # Try to delete
        response = client.delete(
            f"/api/v1/shortlists/{other_shortlist.id}",
            headers=auth_headers,
        )
        assert response.status_code == 403
