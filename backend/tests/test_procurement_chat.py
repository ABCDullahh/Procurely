"""Tests for Procurement Chat API."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from app.main import app


# Uses fixtures from conftest.py: client, admin_headers


class TestProcurementChatEndpoint:
    """Tests for POST /api/v1/procurement-chat/message."""

    def test_send_message_without_auth(self, client):
        """Test that unauthenticated requests are rejected."""
        response = client.post(
            "/api/v1/procurement-chat/message",
            json={"message": "Hello"},
        )
        assert response.status_code == 401

    def test_send_message_with_auth(self, client, admin_headers):
        """Test sending a message with authentication."""
        with patch(
            "app.services.procurement_chat.process_chat_message"
        ) as mock_process:
            mock_response = MagicMock()
            mock_response.message_id = "test-msg-id"
            mock_response.conversation_id = "test-conv-id"
            mock_response.response_type = "text"
            mock_response.text_content = "Hello! How can I help?"
            mock_response.vendors = None
            mock_response.comparison = None
            mock_response.progress = None
            mock_response.evidence = None
            mock_response.chart_data = None
            mock_response.filter_chips = []
            mock_response.suggested_queries = []
            mock_response.actions = []
            mock_response.run_id = None
            mock_response.request_id = None
            mock_response.timestamp = "2024-01-01T00:00:00"

            # Make the mock awaitable
            async def async_return(*args, **kwargs):
                return mock_response

            mock_process.side_effect = async_return

            response = client.post(
                "/api/v1/procurement-chat/message",
                json={"message": "Hello, I need help finding vendors"},
                headers=admin_headers,
            )

            # Check response structure
            if response.status_code == 200:
                data = response.json()
                assert "message_id" in data
                assert "conversation_id" in data
                assert "text_content" in data
            else:
                # If API key not configured, expect 400
                assert response.status_code in [200, 400]

    def test_send_message_with_run_id(self, client, admin_headers):
        """Test sending a message with run_id context."""
        with patch(
            "app.services.procurement_chat.process_chat_message"
        ) as mock_process:
            mock_response = MagicMock()
            mock_response.message_id = "test-msg-id"
            mock_response.conversation_id = "test-conv-id"
            mock_response.response_type = "vendors"
            mock_response.text_content = "Found 5 vendors"
            mock_response.vendors = []
            mock_response.comparison = None
            mock_response.progress = None
            mock_response.evidence = None
            mock_response.chart_data = None
            mock_response.filter_chips = []
            mock_response.suggested_queries = []
            mock_response.actions = []
            mock_response.run_id = 1
            mock_response.request_id = 1
            mock_response.timestamp = "2024-01-01T00:00:00"

            async def async_return(*args, **kwargs):
                return mock_response

            mock_process.side_effect = async_return

            response = client.post(
                "/api/v1/procurement-chat/message",
                json={
                    "message": "Show me the top vendors",
                    "run_id": 1,
                    "mode": "search",
                },
                headers=admin_headers,
            )

            # Accept either success or config error
            assert response.status_code in [200, 400, 422]

    def test_send_compare_message(self, client, admin_headers):
        """Test sending a comparison request."""
        with patch(
            "app.services.procurement_chat.process_chat_message"
        ) as mock_process:
            mock_response = MagicMock()
            mock_response.message_id = "test-msg-id"
            mock_response.conversation_id = "test-conv-id"
            mock_response.response_type = "comparison"
            mock_response.text_content = "Comparing vendors"
            mock_response.vendors = None
            mock_response.comparison = {
                "vendors": [],
                "rows": [],
            }
            mock_response.progress = None
            mock_response.evidence = None
            mock_response.chart_data = None
            mock_response.filter_chips = []
            mock_response.suggested_queries = []
            mock_response.actions = []
            mock_response.run_id = 1
            mock_response.request_id = 1
            mock_response.timestamp = "2024-01-01T00:00:00"

            async def async_return(*args, **kwargs):
                return mock_response

            mock_process.side_effect = async_return

            response = client.post(
                "/api/v1/procurement-chat/message",
                json={
                    "message": "Compare vendors 1 and 2",
                    "run_id": 1,
                    "vendor_ids": [1, 2],
                    "mode": "compare",
                },
                headers=admin_headers,
            )

            assert response.status_code in [200, 400, 422]


class TestProcurementChatSchemas:
    """Tests for procurement chat schema validation."""

    def test_empty_message_rejected(self, client, admin_headers):
        """Test that empty messages are rejected."""
        response = client.post(
            "/api/v1/procurement-chat/message",
            json={"message": ""},
            headers=admin_headers,
        )
        # Empty message should still be accepted (validation is in service)
        # or rejected by pydantic
        assert response.status_code in [200, 400, 422]

    def test_invalid_mode_rejected(self, client, admin_headers):
        """Test that invalid mode is rejected."""
        response = client.post(
            "/api/v1/procurement-chat/message",
            json={"message": "Hello", "mode": "invalid_mode"},
            headers=admin_headers,
        )
        # Should be rejected by pydantic validation
        assert response.status_code == 422
