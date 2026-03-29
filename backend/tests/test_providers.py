"""Tests for provider services."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.errors import (
    ConfigMissingError,
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from app.services.keys import get_active_api_key
from app.services.llm.gemini import GeminiProvider
from app.services.llm.openai import OpenAIProvider
from app.services.providers.base import ProviderStatus, ProviderType, ScrapedPage
from app.services.providers.scrape.jina_reader import JinaReaderProvider
from app.services.providers.scrape.crawl4ai import Crawl4AIProvider
from app.services.providers.scrape.httpx_provider import HttpxProvider
from app.services.providers.search.serper import SerperSearchProvider
from app.services.providers.search.tavily import TavilySearchProvider
from app.services.search.serper import SerperProvider


class TestKeysService:
    """Test API key access service."""

    def test_get_active_api_key_success(self, db, admin_user):
        """Test getting an active API key."""
        from app.core.security import encrypt_api_key
        from app.models.api_key import ApiKey

        # Create a key
        key = ApiKey(
            provider="OPENAI",
            encrypted_value=encrypt_api_key("sk-test-key-12345"),
            masked_tail="*****2345",
            is_active=True,
            updated_by_user_id=admin_user.id,
        )
        db.add(key)
        db.commit()

        result = get_active_api_key(db, "OPENAI")
        assert result == "sk-test-key-12345"

    def test_get_active_api_key_missing(self, db):
        """Test getting a missing API key raises ConfigMissingError."""
        with pytest.raises(ConfigMissingError) as exc_info:
            get_active_api_key(db, "OPENAI")
        assert "OPENAI" in str(exc_info.value)

    def test_get_active_api_key_inactive(self, db, admin_user):
        """Test that inactive keys are not returned."""
        from app.core.security import encrypt_api_key
        from app.models.api_key import ApiKey

        # Create an inactive key
        key = ApiKey(
            provider="OPENAI",
            encrypted_value=encrypt_api_key("sk-inactive"),
            masked_tail="*****tive",
            is_active=False,
            updated_by_user_id=admin_user.id,
        )
        db.add(key)
        db.commit()

        with pytest.raises(ConfigMissingError):
            get_active_api_key(db, "OPENAI")


class TestOpenAIProvider:
    """Test OpenAI provider."""

    @pytest.mark.asyncio
    async def test_complete_text_success(self):
        """Test successful text completion."""
        provider = OpenAIProvider("test-key")

        mock_response = httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "Hello, world!"}}],
                "model": "gpt-4o-mini",
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 5,
                    "total_tokens": 15,
                },
            },
        )

        with patch.object(provider.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await provider.complete_text("Say hello")

        assert result.content == "Hello, world!"
        assert result.model == "gpt-4o-mini"
        assert result.total_tokens == 15
        await provider.close()

    @pytest.mark.asyncio
    async def test_complete_text_auth_error(self):
        """Test authentication error handling."""
        provider = OpenAIProvider("invalid-key")

        mock_response = httpx.Response(401, json={"error": "Invalid API key"})

        with patch.object(provider.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            with pytest.raises(ProviderAuthError):
                await provider.complete_text("Test")
        await provider.close()

    @pytest.mark.asyncio
    async def test_complete_text_rate_limit(self):
        """Test rate limit error handling."""
        provider = OpenAIProvider("test-key")

        mock_response = httpx.Response(
            429,
            headers={"Retry-After": "60"},
            json={"error": "Rate limit exceeded"},
        )

        with patch.object(provider.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            with pytest.raises(ProviderRateLimitError) as exc_info:
                await provider.complete_text("Test")
            assert exc_info.value.retry_after == 60
        await provider.close()

    @pytest.mark.asyncio
    async def test_complete_text_timeout(self):
        """Test timeout error handling."""
        provider = OpenAIProvider("test-key")

        with patch.object(provider.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Timeout")
            with pytest.raises(ProviderTimeoutError):
                await provider.complete_text("Test")
        await provider.close()

    @pytest.mark.asyncio
    async def test_extract_json_success(self):
        """Test successful JSON extraction."""
        provider = OpenAIProvider("test-key")

        mock_response = httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": '{"name": "Acme Corp", "industry": "Software"}'
                        }
                    }
                ],
                "model": "gpt-4o-mini",
                "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            },
        )

        with patch.object(provider.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await provider.extract_json("Extract vendor info")

        assert result["name"] == "Acme Corp"
        assert result["industry"] == "Software"
        await provider.close()


class TestGeminiProvider:
    """Test Gemini provider."""

    @pytest.mark.asyncio
    async def test_complete_text_success(self):
        """Test successful text completion."""
        provider = GeminiProvider("test-key")

        mock_response = httpx.Response(
            200,
            json={
                "candidates": [
                    {"content": {"parts": [{"text": "Hello from Gemini!"}]}}
                ],
                "usageMetadata": {
                    "promptTokenCount": 10,
                    "candidatesTokenCount": 5,
                    "totalTokenCount": 15,
                },
            },
        )

        with patch.object(provider.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await provider.complete_text("Say hello")

        assert result.content == "Hello from Gemini!"
        assert result.total_tokens == 15
        await provider.close()

    @pytest.mark.asyncio
    async def test_complete_text_auth_error(self):
        """Test authentication error handling."""
        provider = GeminiProvider("invalid-key")

        mock_response = httpx.Response(403, json={"error": "Invalid API key"})

        with patch.object(provider.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            with pytest.raises(ProviderAuthError):
                await provider.complete_text("Test")
        await provider.close()


class TestSerperProvider:
    """Test Serper search provider."""

    @pytest.mark.asyncio
    async def test_search_success(self):
        """Test successful search."""
        provider = SerperProvider("test-key")

        mock_response = httpx.Response(
            200,
            json={
                "organic": [
                    {
                        "title": "Acme Corp - Official Website",
                        "link": "https://acme.com",
                        "snippet": "Leading provider of widgets...",
                    },
                    {
                        "title": "Acme Corp Reviews",
                        "link": "https://reviews.com/acme",
                        "snippet": "Read reviews about Acme...",
                    },
                ]
            },
        )

        with patch.object(provider.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            results = await provider.search("Acme Corp vendor")

        assert len(results) == 2
        assert results[0].title == "Acme Corp - Official Website"
        assert results[0].url == "https://acme.com"
        assert results[0].position == 1
        assert results[1].position == 2
        await provider.close()

    @pytest.mark.asyncio
    async def test_search_auth_error(self):
        """Test authentication error handling."""
        provider = SerperProvider("invalid-key")

        mock_response = httpx.Response(401, json={"error": "Invalid API key"})

        with patch.object(provider.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            with pytest.raises(ProviderAuthError):
                await provider.search("Test query")
        await provider.close()

    @pytest.mark.asyncio
    async def test_search_timeout(self):
        """Test timeout error handling."""
        provider = SerperProvider("test-key")

        with patch.object(provider.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Timeout")
            with pytest.raises(ProviderTimeoutError):
                await provider.search("Test query")
        await provider.close()


class TestJinaReaderProvider:
    """Test Jina Reader scrape provider."""

    @pytest.mark.asyncio
    async def test_scrape_success(self):
        """Test successful page scrape."""
        provider = JinaReaderProvider()

        mock_response = httpx.Response(
            200,
            text="# Acme Corp\n\nWe are a leading provider of software solutions.",
        )

        with patch.object(provider.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            result = await provider.scrape("https://acme.com")

        assert result.status == "SUCCESS"
        assert result.content_format == "markdown"
        assert "Acme Corp" in result.content
        assert result.source_provider == "JINA_READER"
        await provider.close()

    @pytest.mark.asyncio
    async def test_scrape_failure(self):
        """Test failed page scrape."""
        provider = JinaReaderProvider()

        mock_response = httpx.Response(404, text="Not Found")

        with patch.object(provider.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            result = await provider.scrape("https://invalid.com")

        assert result.status == "FAILED"
        assert "404" in result.error
        await provider.close()

    @pytest.mark.asyncio
    async def test_scrape_timeout(self):
        """Test timeout handling."""
        provider = JinaReaderProvider()

        with patch.object(provider.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Timeout")
            result = await provider.scrape("https://slow.com")

        assert result.status == "TIMEOUT"
        assert "timed out" in result.error.lower()
        await provider.close()

    @pytest.mark.asyncio
    async def test_scrape_batch(self):
        """Test batch scraping."""
        provider = JinaReaderProvider()

        mock_response = httpx.Response(
            200,
            text="# Test Content\n\nSome content here.",
        )

        with patch.object(provider.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            results = await provider.scrape_batch(
                ["https://example1.com", "https://example2.com"],
                max_concurrent=2,
            )

        assert len(results) == 2
        assert all(r.status == "SUCCESS" for r in results)
        await provider.close()


class TestCrawl4AIProvider:
    """Test Crawl4AI scrape provider."""

    @pytest.mark.asyncio
    async def test_scrape_success(self):
        """Test successful page scrape."""
        provider = Crawl4AIProvider("http://localhost:11235")

        mock_response = httpx.Response(
            200,
            json={
                "results": [
                    {
                        "success": True,
                        "title": "Acme Corp",
                        "markdown": "# Acme Corp\n\nBest software company.",
                        "word_count": 10,
                        "links": [],
                    }
                ]
            },
        )

        with patch.object(provider.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await provider.scrape("https://acme.com")

        assert result.status == "SUCCESS"
        assert result.title == "Acme Corp"
        assert "Acme Corp" in result.content
        assert result.source_provider == "CRAWL4AI"
        await provider.close()

    @pytest.mark.asyncio
    async def test_scrape_failure(self):
        """Test failed page scrape."""
        provider = Crawl4AIProvider("http://localhost:11235")

        mock_response = httpx.Response(
            200,
            json={
                "results": [
                    {
                        "success": False,
                        "error": "Failed to fetch page",
                    }
                ]
            },
        )

        with patch.object(provider.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await provider.scrape("https://invalid.com")

        assert result.status == "FAILED"
        assert "Failed to fetch" in result.error
        await provider.close()

    @pytest.mark.asyncio
    async def test_scrape_service_unavailable(self):
        """Test handling when Crawl4AI service is not available."""
        provider = Crawl4AIProvider("http://localhost:11235")

        with patch.object(provider.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection refused")
            result = await provider.scrape("https://example.com")

        assert result.status == "SERVICE_UNAVAILABLE"
        assert "not available" in result.error.lower()
        await provider.close()


class TestHttpxProvider:
    """Test legacy httpx scrape provider."""

    @pytest.mark.asyncio
    async def test_scrape_success(self):
        """Test successful page scrape."""
        provider = HttpxProvider()

        html_content = """
        <html>
            <head><title>Acme Corp</title></head>
            <body>
                <h1>Welcome to Acme Corp</h1>
                <p>We provide great services.</p>
            </body>
        </html>
        """
        mock_response = httpx.Response(
            200,
            text=html_content,
            headers={"content-type": "text/html"},
        )

        with patch.object(provider.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            result = await provider.scrape("https://acme.com")

        assert result.status == "SUCCESS"
        assert result.title == "Acme Corp"
        assert "Welcome to Acme Corp" in result.content
        assert result.source_provider == "HTTPX"
        await provider.close()

    @pytest.mark.asyncio
    async def test_scrape_non_html(self):
        """Test handling of non-HTML content."""
        provider = HttpxProvider()

        mock_response = httpx.Response(
            200,
            text="plain text content",
            headers={"content-type": "text/plain"},
        )

        with patch.object(provider.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            result = await provider.scrape("https://example.com/file.txt")

        assert result.status == "SUCCESS"
        assert result.content == "plain text content"
        await provider.close()


class TestSerperSearchProvider:
    """Test Serper search provider (new registry pattern)."""

    @pytest.mark.asyncio
    async def test_search_success(self):
        """Test successful search."""
        provider = SerperSearchProvider("test-key")

        mock_response = httpx.Response(
            200,
            json={
                "organic": [
                    {
                        "title": "Acme Corp - Official Website",
                        "link": "https://acme.com",
                        "snippet": "Leading provider of widgets...",
                    },
                    {
                        "title": "Acme Corp Reviews",
                        "link": "https://reviews.com/acme",
                        "snippet": "Read reviews about Acme...",
                    },
                ]
            },
        )

        with patch.object(provider.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            results = await provider.search("Acme Corp vendor")

        assert len(results) == 2
        assert results[0].title == "Acme Corp - Official Website"
        assert results[0].url == "https://acme.com"
        assert results[0].source_provider == "SERPER"
        await provider.close()


class TestTavilySearchProvider:
    """Test Tavily search provider."""

    @pytest.mark.asyncio
    async def test_search_success(self):
        """Test successful search."""
        provider = TavilySearchProvider("test-key")

        mock_response = httpx.Response(
            200,
            json={
                "results": [
                    {
                        "url": "https://acme.com",
                        "title": "Acme Corp",
                        "content": "Leading software company...",
                    },
                    {
                        "url": "https://reviews.com/acme",
                        "title": "Acme Reviews",
                        "content": "Customer reviews...",
                    },
                ]
            },
        )

        with patch.object(provider.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            results = await provider.search("Acme Corp")

        assert len(results) == 2
        assert results[0].url == "https://acme.com"
        assert results[0].source_provider == "TAVILY"
        await provider.close()

    @pytest.mark.asyncio
    async def test_search_auth_error(self):
        """Test authentication error handling."""
        provider = TavilySearchProvider("invalid-key")

        mock_response = httpx.Response(401, json={"error": "Invalid API key"})

        with patch.object(provider.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            with pytest.raises(ProviderAuthError):
                await provider.search("Test query")
        await provider.close()
