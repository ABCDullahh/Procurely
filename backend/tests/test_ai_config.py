"""Tests for AI configuration endpoints."""



class TestAIConfig:
    """Test AI configuration endpoints."""

    def test_get_ai_config_defaults(self, admin_headers, client):
        """Test getting AI config returns defaults when not set."""
        response = client.get(
            "/api/v1/admin/settings/ai-config",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()

        # Check structure
        assert "web_search" in data
        assert "procurement_llm" in data
        assert "copilot_llm" in data
        assert "available_search_providers" in data

        # Check defaults
        assert data["web_search"]["provider"] == "SERPER"
        assert data["procurement_llm"]["provider"] == "OPENAI"
        assert data["copilot_llm"]["provider"] == "GEMINI"

        # Keys not configured by default
        assert data["web_search"]["key_configured"] is False
        assert data["procurement_llm"]["key_configured"] is False
        assert data["copilot_llm"]["key_configured"] is False

    def test_set_ai_config_requires_key(self, admin_headers, client):
        """Test that setting provider requires API key to be configured."""
        # Try to set TAVILY without TAVILY key
        response = client.put(
            "/api/v1/admin/settings/ai-config",
            headers=admin_headers,
            json={"web_search_provider": "TAVILY"}
        )
        assert response.status_code == 400
        assert "TAVILY API key" in response.json()["detail"]

    def test_set_ai_config_with_valid_key(self, admin_headers, client):
        """Test setting config when key is configured."""
        # First configure GEMINI key
        client.put(
            "/api/v1/admin/api-keys/GEMINI",
            headers=admin_headers,
            json={"value": "test-gemini-key-123456789"}
        )

        # Now set copilot to use GEMINI
        response = client.put(
            "/api/v1/admin/settings/ai-config",
            headers=admin_headers,
            json={
                "copilot_provider": "GEMINI",
                "copilot_model": "gemini-1.5-pro"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["copilot_llm"]["provider"] == "GEMINI"
        assert data["copilot_llm"]["model"] == "gemini-1.5-pro"
        assert data["copilot_llm"]["key_configured"] is True

    def test_set_procurement_llm(self, admin_headers, client):
        """Test setting procurement LLM config."""
        # Configure OPENAI key
        client.put(
            "/api/v1/admin/api-keys/OPENAI",
            headers=admin_headers,
            json={"value": "sk-test12345678901234567890"}
        )

        # Set procurement LLM
        response = client.put(
            "/api/v1/admin/settings/ai-config",
            headers=admin_headers,
            json={
                "procurement_provider": "OPENAI",
                "procurement_model": "gpt-4o"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["procurement_llm"]["provider"] == "OPENAI"
        assert data["procurement_llm"]["model"] == "gpt-4o"

    def test_non_admin_cannot_access(self, auth_headers, client):
        """Test that non-admin users cannot access AI config."""
        response = client.get(
            "/api/v1/admin/settings/ai-config",
            headers=auth_headers
        )
        assert response.status_code == 403

    def test_available_search_providers(self, admin_headers, client):
        """Test that available search providers are returned."""
        response = client.get(
            "/api/v1/admin/settings/ai-config",
            headers=admin_headers
        )
        assert response.status_code == 200
        providers = response.json()["available_search_providers"]

        # Check all providers are listed
        values = [p["value"] for p in providers]
        assert "SERPER" in values
        assert "TAVILY" in values
        assert "GEMINI_GROUNDING" in values
