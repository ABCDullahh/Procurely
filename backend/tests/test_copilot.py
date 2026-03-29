"""Tests for copilot API endpoint."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models import (
    ProcurementRequest,
    SearchRun,
    User,
    Vendor,
    VendorMetrics,
    VendorSource,
)
from app.services.errors import ConfigMissingError


@pytest.fixture
def client():
    """Get test client."""
    return TestClient(app)


class TestCopilotEndpoint:
    """Tests for POST /api/v1/copilot/chat."""

    @pytest.fixture
    def completed_run_with_vendors(self, db, test_user):
        """Create a completed run with vendors for copilot testing."""
        # Create request
        request = ProcurementRequest(
            title="Copilot Test Request",
            category="Software",
            keywords=json.dumps(["copilot", "test"]),
            must_have_criteria=json.dumps(["API"]),
            nice_to_have_criteria=json.dumps(["Support"]),
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
        vendor1 = Vendor(
            name="Test Vendor 1",
            website="https://vendor1.com",
            location="New York",
            industry="SaaS",
        )
        vendor2 = Vendor(
            name="Test Vendor 2",
            website="https://vendor2.com",
            location="London",
            industry="Enterprise",
        )
        db.add_all([vendor1, vendor2])
        db.commit()
        db.refresh(vendor1)
        db.refresh(vendor2)

        # Add sources
        source1 = VendorSource(
            vendor_id=vendor1.id,
            search_run_id=run.id,
            source_url="https://source1.com",
            source_type="WEB",
        )
        source2 = VendorSource(
            vendor_id=vendor2.id,
            search_run_id=run.id,
            source_url="https://source2.com",
            source_type="WEB",
        )
        db.add_all([source1, source2])

        # Add metrics
        metrics1 = VendorMetrics(
            vendor_id=vendor1.id,
            search_run_id=run.id,
            overall_score=85.0,
            fit_score=80.0,
            trust_score=90.0,
        )
        metrics2 = VendorMetrics(
            vendor_id=vendor2.id,
            search_run_id=run.id,
            overall_score=75.0,
            fit_score=70.0,
            trust_score=80.0,
        )
        db.add_all([metrics1, metrics2])
        db.commit()

        return {
            "run": run,
            "request": request,
            "vendors": [vendor1, vendor2],
        }

    def test_copilot_rbac_forbidden(
        self, client: TestClient, db, completed_run_with_vendors
    ):
        """Test user cannot access another user's run."""
        run_id = completed_run_with_vendors["run"].id

        # Create another user
        other_user = User(
            email="other_copilot@example.com",
            password_hash=get_password_hash("password"),
            full_name="Other User",
        )
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        # Get token for other user
        other_token = create_access_token(other_user.id)
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # Try to access as other user
        response = client.post(
            "/api/v1/copilot/chat",
            json={
                "run_id": run_id,
                "message": "What are the top vendors?",
            },
            headers=other_headers,
        )
        assert response.status_code == 403

    @patch("app.services.keys.get_active_api_key_with_model")
    @patch("app.services.copilot.OpenAIProvider")
    def test_copilot_returns_structured_response(
        self,
        mock_openai_provider_class,
        mock_get_key,
        client: TestClient,
        auth_headers: dict,
        completed_run_with_vendors,
    ):
        """Test copilot returns answer with citations and actions."""
        run_id = completed_run_with_vendors["run"].id

        # Mock API key retrieval
        mock_get_key.return_value = ("test-api-key", "gpt-4o")

        # Mock LLM response
        mock_response = json.dumps(
            {
                "answer": "Based on the analysis, Test Vendor 1 is the best.",
                "citations": [
                    {
                        "vendor_id": completed_run_with_vendors["vendors"][0].id,
                        "vendor_name": "Test Vendor 1",
                        "source_url": "https://source1.com",
                        "snippet": "High quality vendor",
                        "field_name": "features",
                    }
                ],
                "suggested_actions": [
                    {
                        "type": "OPEN_VENDOR",
                        "label": "View Test Vendor 1",
                        "payload": {
                            "vendor_id": completed_run_with_vendors["vendors"][0].id
                        },
                    }
                ],
            }
        )

        # Setup mock provider
        mock_provider_instance = MagicMock()
        mock_provider_instance.complete_text = AsyncMock(return_value=mock_response)
        mock_openai_provider_class.return_value = mock_provider_instance

        response = client.post(
            "/api/v1/copilot/chat",
            json={
                "run_id": run_id,
                "message": "What is the best vendor?",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert "answer" in data
        assert "Test Vendor 1" in data["answer"]
        assert "citations" in data
        assert len(data["citations"]) >= 1
        assert data["citations"][0]["vendor_name"] == "Test Vendor 1"
        assert "suggested_actions" in data
        assert len(data["suggested_actions"]) >= 1
        assert data["suggested_actions"][0]["type"] == "OPEN_VENDOR"

    @patch("app.services.keys.get_active_api_key_with_model")
    def test_copilot_handles_missing_key(
        self,
        mock_get_key,
        client: TestClient,
        auth_headers: dict,
        completed_run_with_vendors,
    ):
        """Test copilot returns 400 when API key is missing."""
        run_id = completed_run_with_vendors["run"].id

        # Mock provider raising config error for both OpenAI and Gemini
        mock_get_key.side_effect = ConfigMissingError("No API key")

        response = client.post(
            "/api/v1/copilot/chat",
            json={
                "run_id": run_id,
                "message": "What are the top vendors?",
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "not configured" in response.json()["detail"]

    @patch("app.services.keys.get_active_api_key_with_model")
    @patch("app.services.copilot.OpenAIProvider")
    def test_copilot_vendor_ids_filter_context(
        self,
        mock_openai_provider_class,
        mock_get_key,
        client: TestClient,
        auth_headers: dict,
        completed_run_with_vendors,
    ):
        """Test copilot filters context to specific vendor IDs."""
        run_id = completed_run_with_vendors["run"].id
        vendor1_id = completed_run_with_vendors["vendors"][0].id

        # Mock API key
        mock_get_key.return_value = ("test-api-key", "gpt-4o")

        # Mock LLM response
        mock_response = json.dumps(
            {
                "answer": "Analyzing only Test Vendor 1 as requested.",
                "citations": [],
                "suggested_actions": [],
            }
        )

        mock_provider_instance = MagicMock()
        mock_provider_instance.complete_text = AsyncMock(return_value=mock_response)
        mock_openai_provider_class.return_value = mock_provider_instance

        response = client.post(
            "/api/v1/copilot/chat",
            json={
                "run_id": run_id,
                "message": "Analyze this vendor",
                "vendor_ids": [vendor1_id],
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data

        # Verify the provider was used
        mock_provider_instance.complete_text.assert_called_once()

    def test_copilot_run_not_found(self, client: TestClient, auth_headers: dict):
        """Test copilot returns 404 for non-existent run."""
        response = client.post(
            "/api/v1/copilot/chat",
            json={
                "run_id": 99999,
                "message": "Hello",
            },
            headers=auth_headers,
        )
        assert response.status_code == 404
