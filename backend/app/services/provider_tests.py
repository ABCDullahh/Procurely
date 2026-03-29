"""Provider test service for testing API key connectivity."""

import time
from typing import NamedTuple

import httpx

from app.schemas.api_key import ApiKeyTestResponse


class TestResult(NamedTuple):
    """Result of a provider test."""

    ok: bool
    message: str
    latency_ms: int | None


async def test_openai_key(api_key: str) -> TestResult:
    """Test OpenAI API key by calling the models endpoint.

    This is a lightweight endpoint that validates the key without
    consuming significant API credits.
    """
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            latency_ms = int((time.monotonic() - start) * 1000)

            if response.status_code == 200:
                return TestResult(
                    ok=True,
                    message="OpenAI API key is valid",
                    latency_ms=latency_ms,
                )
            elif response.status_code == 401:
                return TestResult(
                    ok=False,
                    message="Invalid API key",
                    latency_ms=latency_ms,
                )
            elif response.status_code == 429:
                return TestResult(
                    ok=False,
                    message="Rate limited - key may be valid but quota exceeded",
                    latency_ms=latency_ms,
                )
            else:
                return TestResult(
                    ok=False,
                    message=f"Unexpected status: {response.status_code}",
                    latency_ms=latency_ms,
                )
    except httpx.TimeoutException:
        latency_ms = int((time.monotonic() - start) * 1000)
        return TestResult(
            ok=False,
            message="Connection timeout",
            latency_ms=latency_ms,
        )
    except Exception as e:
        return TestResult(
            ok=False,
            message=f"Connection error: {str(e)}",
            latency_ms=None,
        )


async def test_gemini_key(api_key: str) -> TestResult:
    """Test Google Gemini API key by calling the models endpoint.

    Uses the Generative AI API models list endpoint for validation.
    """
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}",
            )
            latency_ms = int((time.monotonic() - start) * 1000)

            if response.status_code == 200:
                return TestResult(
                    ok=True,
                    message="Gemini API key is valid",
                    latency_ms=latency_ms,
                )
            elif response.status_code == 400:
                error = response.json().get("error", {})
                msg = error.get("message", "Invalid API key")
                return TestResult(
                    ok=False,
                    message=msg,
                    latency_ms=latency_ms,
                )
            elif response.status_code == 403:
                return TestResult(
                    ok=False,
                    message="API key lacks permission or is disabled",
                    latency_ms=latency_ms,
                )
            else:
                return TestResult(
                    ok=False,
                    message=f"Unexpected status: {response.status_code}",
                    latency_ms=latency_ms,
                )
    except httpx.TimeoutException:
        latency_ms = int((time.monotonic() - start) * 1000)
        return TestResult(
            ok=False,
            message="Connection timeout",
            latency_ms=latency_ms,
        )
    except Exception as e:
        return TestResult(
            ok=False,
            message=f"Connection error: {str(e)}",
            latency_ms=None,
        )


async def test_search_provider_key(api_key: str) -> TestResult:
    """Test Serper search provider API key.

    Tests the Serper.dev API by making a minimal search request.
    """
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": api_key},
                json={"q": "test", "num": 1},
            )
            latency_ms = int((time.monotonic() - start) * 1000)

            if response.status_code == 200:
                return TestResult(
                    ok=True,
                    message="Serper API key is valid",
                    latency_ms=latency_ms,
                )
            elif response.status_code == 401 or response.status_code == 403:
                return TestResult(
                    ok=False,
                    message="Invalid Serper API key",
                    latency_ms=latency_ms,
                )
            elif response.status_code == 429:
                return TestResult(
                    ok=False,
                    message="Rate limited - key may be valid but quota exceeded",
                    latency_ms=latency_ms,
                )
            else:
                return TestResult(
                    ok=False,
                    message=f"Unexpected status: {response.status_code}",
                    latency_ms=latency_ms,
                )
    except httpx.TimeoutException:
        latency_ms = int((time.monotonic() - start) * 1000)
        return TestResult(
            ok=False,
            message="Connection timeout",
            latency_ms=latency_ms,
        )
    except Exception as e:
        return TestResult(
            ok=False,
            message=f"Connection error: {str(e)}",
            latency_ms=None,
        )


async def test_tavily_key(api_key: str) -> TestResult:
    """Test Tavily API key by calling the search endpoint.

    Tavily API uses the api_key in the request body, not as a header.
    We make a minimal search request to validate the key.

    Tavily API keys typically start with 'tvly-'.
    """
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Tavily uses POST with api_key in body
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": "test",
                    "max_results": 1,
                    "search_depth": "basic",
                },
            )
            latency_ms = int((time.monotonic() - start) * 1000)

            if response.status_code == 200:
                return TestResult(
                    ok=True,
                    message="Tavily API key is valid",
                    latency_ms=latency_ms,
                )
            elif response.status_code == 401:
                return TestResult(
                    ok=False,
                    message="Invalid Tavily API key. Keys should start with 'tvly-'",
                    latency_ms=latency_ms,
                )
            elif response.status_code == 400:
                # Check if it's an API key error
                try:
                    error_data = response.json()
                    error_msg = error_data.get("detail", str(error_data))
                    if "api_key" in str(error_msg).lower() or "invalid" in str(error_msg).lower():
                        return TestResult(
                            ok=False,
                            message=f"Invalid API key: {error_msg}",
                            latency_ms=latency_ms,
                        )
                except Exception:
                    pass
                return TestResult(
                    ok=False,
                    message=f"API error: {response.text[:100]}",
                    latency_ms=latency_ms,
                )
            elif response.status_code == 429:
                return TestResult(
                    ok=False,
                    message="Rate limited - key may be valid but quota exceeded",
                    latency_ms=latency_ms,
                )
            else:
                return TestResult(
                    ok=False,
                    message=f"Unexpected status: {response.status_code} - {response.text[:100]}",
                    latency_ms=latency_ms,
                )
    except httpx.TimeoutException:
        latency_ms = int((time.monotonic() - start) * 1000)
        return TestResult(
            ok=False,
            message="Connection timeout - check your network connection",
            latency_ms=latency_ms,
        )
    except httpx.ConnectError:
        return TestResult(
            ok=False,
            message="Connection failed: Unable to reach Tavily API. Check your network.",
            latency_ms=None,
        )
    except Exception as e:
        return TestResult(
            ok=False,
            message=f"Connection error: {str(e)}",
            latency_ms=None,
        )


async def test_serpapi_key(api_key: str) -> TestResult:
    """Test SerpAPI key for Google Shopping integration.

    SerpAPI uses the api_key as a query parameter.
    """
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://serpapi.com/account",
                params={"api_key": api_key},
            )
            latency_ms = int((time.monotonic() - start) * 1000)

            if response.status_code == 200:
                data = response.json()
                searches_left = data.get("total_searches_left", "unknown")
                return TestResult(
                    ok=True,
                    message=f"SerpAPI key valid. Searches remaining: {searches_left}",
                    latency_ms=latency_ms,
                )
            elif response.status_code == 401:
                return TestResult(
                    ok=False,
                    message="Invalid SerpAPI key",
                    latency_ms=latency_ms,
                )
            else:
                return TestResult(
                    ok=False,
                    message=f"Unexpected status: {response.status_code}",
                    latency_ms=latency_ms,
                )
    except httpx.TimeoutException:
        latency_ms = int((time.monotonic() - start) * 1000)
        return TestResult(
            ok=False,
            message="Connection timeout",
            latency_ms=latency_ms,
        )
    except Exception as e:
        return TestResult(
            ok=False,
            message=f"Connection error: {str(e)}",
            latency_ms=None,
        )


async def test_provider_key(provider: str, api_key: str) -> ApiKeyTestResponse:
    """Test an API key for a given provider.

    Args:
        provider: Provider name (OPENAI, GEMINI, SEARCH_PROVIDER, TAVILY, SERPAPI, FIRECRAWL)
        api_key: Decrypted API key value

    Returns:
        ApiKeyTestResponse with test results
    """
    if provider == "OPENAI":
        result = await test_openai_key(api_key)
    elif provider == "GEMINI":
        result = await test_gemini_key(api_key)
    elif provider == "SEARCH_PROVIDER":
        result = await test_search_provider_key(api_key)
    elif provider == "TAVILY":
        result = await test_tavily_key(api_key)
    elif provider == "SERPAPI":
        result = await test_serpapi_key(api_key)
    elif provider == "FIRECRAWL":
        # Firecrawl test - basic validation for now
        if len(api_key) < 10:
            result = TestResult(
                ok=False,
                message="API key appears too short",
                latency_ms=None,
            )
        else:
            result = TestResult(
                ok=True,
                message="Firecrawl API key stored (live test not implemented)",
                latency_ms=None,
            )
    else:
        result = TestResult(
            ok=False,
            message=f"Unknown provider: {provider}",
            latency_ms=None,
        )

    return ApiKeyTestResponse(
        ok=result.ok,
        message=result.message,
        provider=provider,
        latency_ms=result.latency_ms,
    )
