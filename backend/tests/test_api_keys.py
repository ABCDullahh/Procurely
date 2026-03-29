"""Tests for API key CRUD and encryption."""


from app.models.api_key import ApiKey
from app.models.audit_log import AuditLog


class TestApiKeyCrud:
    """Test API key CRUD operations."""

    def test_list_api_keys_empty(self, admin_headers, client):
        """Test listing API keys when none exist."""
        response = client.get("/api/v1/admin/api-keys", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["keys"] == []

    def test_set_api_key(self, admin_headers, client):
        """Test setting a new API key."""
        response = client.put(
            "/api/v1/admin/api-keys/OPENAI",
            headers=admin_headers,
            json={"value": "sk-test12345678901234567890"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "OPENAI"
        assert data["is_active"] is True
        assert data["masked_tail"].endswith("7890")

    def test_get_api_key(self, db, admin_user, admin_headers, client):
        """Test getting a specific API key after setting it."""
        # Set key via API first
        client.put(
            "/api/v1/admin/api-keys/GEMINI",
            headers=admin_headers,
            json={"value": "test-gemini-key-123456789"},
        )

        response = client.get("/api/v1/admin/api-keys/GEMINI", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "GEMINI"

    def test_rotate_api_key(self, admin_headers, client):
        """Test rotating an API key."""
        # First set a key
        client.put(
            "/api/v1/admin/api-keys/OPENAI",
            headers=admin_headers,
            json={"value": "sk-oldkey123456789012345678"},
        )

        # Then rotate it
        response = client.post(
            "/api/v1/admin/api-keys/OPENAI/rotate",
            headers=admin_headers,
            json={"value": "sk-newkey987654321098765432"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["masked_tail"].endswith("5432")

    def test_delete_api_key(self, admin_headers, client):
        """Test deleting an API key."""
        # First set a key
        client.put(
            "/api/v1/admin/api-keys/OPENAI",
            headers=admin_headers,
            json={"value": "sk-deletetest1234567890123"},
        )

        # Then delete it
        response = client.delete("/api/v1/admin/api-keys/OPENAI", headers=admin_headers)
        assert response.status_code == 204

        # Verify it's gone
        response = client.get("/api/v1/admin/api-keys/OPENAI", headers=admin_headers)
        assert response.status_code == 404

    def test_non_admin_cannot_access(self, auth_headers, client):
        """Test that non-admin users cannot access API keys endpoints."""
        response = client.get("/api/v1/admin/api-keys", headers=auth_headers)
        assert response.status_code == 403


class TestApiKeyEncryption:
    """Test API key encryption."""

    def test_key_is_encrypted_in_db(self, db, admin_headers, client):
        """Test that API keys are encrypted in the database."""
        # Set a key
        client.put(
            "/api/v1/admin/api-keys/OPENAI",
            headers=admin_headers,
            json={"value": "sk-plaintext1234567890123"},
        )

        # Check DB directly
        key = db.query(ApiKey).filter(ApiKey.provider == "OPENAI").first()
        assert key is not None
        # Encrypted value should not contain plaintext
        assert "sk-plaintext" not in key.encrypted_value
        # Encrypted value should be hex
        assert all(c in "0123456789abcdef" for c in key.encrypted_value)


class TestAuditLogs:
    """Test audit logging."""

    def test_audit_log_created_on_set(self, db, admin_headers, client):
        """Test that audit log is created when setting a key."""
        client.put(
            "/api/v1/admin/api-keys/OPENAI",
            headers=admin_headers,
            json={"value": "sk-audit12345678901234567"},
        )

        log = db.query(AuditLog).filter(AuditLog.action == "API_KEY_SET").first()
        assert log is not None
        assert log.target_type == "api_key"

    def test_audit_log_created_on_rotate(self, admin_headers, db, client):
        """Test that audit log is created when rotating a key."""
        # Set initial key
        client.put(
            "/api/v1/admin/api-keys/OPENAI",
            headers=admin_headers,
            json={"value": "sk-init123456789012345678"},
        )

        # Rotate
        client.post(
            "/api/v1/admin/api-keys/OPENAI/rotate",
            headers=admin_headers,
            json={"value": "sk-new1234567890123456789"},
        )

        log = db.query(AuditLog).filter(AuditLog.action == "API_KEY_ROTATE").first()
        assert log is not None
