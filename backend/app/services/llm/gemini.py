"""Google Gemini LLM provider implementation."""

import json
import logging
from typing import Any

import httpx

from app.services.errors import (
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderTokenLimitError,
)
from app.services.llm.base import LLMConfig, LLMJsonResponse, LLMProvider, LLMResponse

logger = logging.getLogger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider using httpx."""

    provider_name = "GEMINI"

    def __init__(self, api_key: str, default_model: str | None = None):
        """Initialize with API key and optional default model."""
        self.api_key = api_key
        self._default_model = default_model or "gemini-2.0-flash-exp"
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(180.0, connect=10.0),
            headers={"Content-Type": "application/json"},
        )

    def _get_url(self, model: str) -> str:
        """Get API URL for model."""
        return f"{GEMINI_API_URL}/{model}:generateContent?key={self.api_key}"

    async def complete_text(
        self,
        prompt: str,
        config: LLMConfig | None = None,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """Generate text completion using Gemini API."""
        cfg = config or self.get_default_config()

        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": system_prompt}]})
            contents.append({"role": "model", "parts": [{"text": "Understood."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": cfg.temperature,
                "maxOutputTokens": cfg.max_tokens,
            },
        }

        try:
            response = await self.client.post(
                self._get_url(cfg.model),
                json=payload,
                timeout=cfg.timeout_seconds,
            )
        except httpx.TimeoutException:
            raise ProviderTimeoutError(self.provider_name, cfg.timeout_seconds)
        except httpx.RequestError as e:
            raise ProviderResponseError(self.provider_name, 0, str(e))

        if response.status_code == 401 or response.status_code == 403:
            raise ProviderAuthError(self.provider_name, "Invalid API key")
        if response.status_code == 429:
            raise ProviderRateLimitError(self.provider_name, None)
        if response.status_code != 200:
            raise ProviderResponseError(
                self.provider_name,
                response.status_code,
                response.text[:500],
            )

        data = response.json()

        # Handle safety blocks
        if "candidates" not in data or not data["candidates"]:
            raise ProviderResponseError(
                self.provider_name,
                200,
                "No candidates in response (possibly blocked by safety)",
            )

        candidate = data["candidates"][0]
        finish_reason = candidate.get("finishReason", "")

        # First, try to extract content - even MAX_TOKENS responses often have usable content
        if "content" not in candidate:
            raise ProviderResponseError(
                self.provider_name,
                200,
                f"No content in candidate: {finish_reason}",
            )

        # Safely extract text from parts
        try:
            parts = candidate["content"].get("parts", [])
            if not parts:
                # No parts returned - check if it's a token limit issue
                if finish_reason == "MAX_TOKENS":
                    raise ProviderTokenLimitError(
                        self.provider_name,
                        "Output was truncated - no text parts returned"
                    )
                raise ProviderResponseError(
                    self.provider_name,
                    200,
                    f"No parts in response content: {finish_reason}",
                )
            content = parts[0].get("text", "")
            if not content:
                if finish_reason == "MAX_TOKENS":
                    raise ProviderTokenLimitError(
                        self.provider_name,
                        "Output was truncated - empty text returned"
                    )
                raise ProviderResponseError(
                    self.provider_name,
                    200,
                    "Empty text in response parts",
                )

            # Log if truncated but we got content (this is OK - we can use partial content)
            if finish_reason == "MAX_TOKENS":
                logger.warning(
                    f"Gemini response was truncated (MAX_TOKENS) but got {len(content)} chars. "
                    "Using partial content."
                )
        except (KeyError, IndexError, TypeError) as e:
            raise ProviderResponseError(
                self.provider_name,
                200,
                f"Invalid response structure: {str(e)}",
            )

        usage = data.get("usageMetadata", {})

        return LLMResponse(
            content=content,
            model=cfg.model,
            prompt_tokens=usage.get("promptTokenCount", 0),
            completion_tokens=usage.get("candidatesTokenCount", 0),
            total_tokens=usage.get("totalTokenCount", 0),
        )

    async def extract_json(
        self,
        prompt: str,
        schema_hint: str | None = None,
        config: LLMConfig | None = None,
    ) -> dict[str, Any]:
        """Extract structured JSON using Gemini."""
        cfg = config or self.get_default_config()

        system_instruction = (
            "You are a helpful assistant that extracts information. "
            "Always respond with valid JSON only, no markdown, no explanation. "
            "Keep responses concise to avoid truncation."
        )
        if schema_hint:
            system_instruction += f"\n\nExpected JSON schema:\n{schema_hint}"

        full_prompt = f"{system_instruction}\n\n{prompt}"

        response = await self.complete_text(
            full_prompt,
            config=LLMConfig(
                model=cfg.model,
                temperature=0.1,
                max_tokens=cfg.max_tokens,
                timeout_seconds=cfg.timeout_seconds,
            ),
        )

        content = response.content.strip()
        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from Gemini: {e}")
            # Try to repair truncated JSON
            repaired = self._repair_truncated_json(content)
            if repaired:
                try:
                    return json.loads(repaired)
                except json.JSONDecodeError:
                    pass
            raise ProviderResponseError(
                self.provider_name,
                200,
                f"Invalid JSON response: {content[:200]}",
            )

    async def extract_json_with_tokens(
        self,
        prompt: str,
        schema_hint: str | None = None,
        config: LLMConfig | None = None,
    ) -> LLMJsonResponse:
        """Extract structured JSON using Gemini with token tracking."""
        cfg = config or self.get_default_config()

        system_instruction = (
            "You are a helpful assistant that extracts information. "
            "Always respond with valid JSON only, no markdown, no explanation. "
            "Keep responses concise to avoid truncation."
        )
        if schema_hint:
            system_instruction += f"\n\nExpected JSON schema:\n{schema_hint}"

        full_prompt = f"{system_instruction}\n\n{prompt}"

        response = await self.complete_text(
            full_prompt,
            config=LLMConfig(
                model=cfg.model,
                temperature=0.1,
                max_tokens=cfg.max_tokens,
                timeout_seconds=cfg.timeout_seconds,
            ),
        )

        content = response.content.strip()
        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        try:
            parsed_data = json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from Gemini: {e}")
            # Try to repair truncated JSON
            repaired = self._repair_truncated_json(content)
            if repaired:
                try:
                    parsed_data = json.loads(repaired)
                except json.JSONDecodeError:
                    raise ProviderResponseError(
                        self.provider_name,
                        200,
                        f"Invalid JSON response: {content[:200]}",
                    )
            else:
                raise ProviderResponseError(
                    self.provider_name,
                    200,
                    f"Invalid JSON response: {content[:200]}",
                )

        return LLMJsonResponse(
            data=parsed_data,
            model=response.model,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            total_tokens=response.total_tokens,
        )

    def _repair_truncated_json(self, content: str) -> str | None:
        """Attempt to repair truncated JSON by closing open brackets/braces."""
        if not content:
            return None

        # Count open brackets
        open_braces = content.count('{') - content.count('}')
        open_brackets = content.count('[') - content.count(']')

        # If we have more opens than closes, try to close them
        if open_braces > 0 or open_brackets > 0:
            # Find the last complete key-value or element
            # Truncate at the last comma if present
            last_comma = content.rfind(',')
            if last_comma > 0:
                content = content[:last_comma]

            # Close any open brackets/braces
            content += ']' * open_brackets
            content += '}' * open_braces
            return content

        return None

    def get_default_model(self) -> str:
        """Get default Gemini model."""
        return self._default_model

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
