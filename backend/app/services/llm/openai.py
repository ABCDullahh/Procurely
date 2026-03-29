"""OpenAI LLM provider implementation."""

import json
import logging
from typing import Any

import httpx

from app.services.errors import (
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderResponseError,
    ProviderTimeoutError,
)
from app.services.llm.base import LLMConfig, LLMJsonResponse, LLMProvider, LLMResponse

logger = logging.getLogger(__name__)

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider using httpx."""

    provider_name = "OPENAI"

    def __init__(self, api_key: str, default_model: str | None = None):
        """Initialize with API key and optional default model."""
        self.api_key = api_key
        self._default_model = default_model or "gpt-4o-mini"
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=10.0),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

    async def complete_text(
        self,
        prompt: str,
        config: LLMConfig | None = None,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """Generate text completion using OpenAI API."""
        cfg = config or self.get_default_config()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": cfg.model,
            "messages": messages,
            "temperature": cfg.temperature,
            "max_tokens": cfg.max_tokens,
        }

        try:
            response = await self.client.post(
                OPENAI_API_URL,
                json=payload,
                timeout=cfg.timeout_seconds,
            )
        except httpx.TimeoutException:
            raise ProviderTimeoutError(self.provider_name, cfg.timeout_seconds)
        except httpx.RequestError as e:
            raise ProviderResponseError(self.provider_name, 0, str(e))

        if response.status_code == 401:
            raise ProviderAuthError(self.provider_name, "Invalid API key")
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise ProviderRateLimitError(
                self.provider_name,
                int(retry_after) if retry_after else None,
            )
        if response.status_code != 200:
            raise ProviderResponseError(
                self.provider_name,
                response.status_code,
                response.text[:500],
            )

        data = response.json()
        choice = data["choices"][0]
        usage = data.get("usage", {})

        return LLMResponse(
            content=choice["message"]["content"],
            model=data["model"],
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        )

    async def extract_json(
        self,
        prompt: str,
        schema_hint: str | None = None,
        config: LLMConfig | None = None,
    ) -> dict[str, Any]:
        """Extract structured JSON using OpenAI JSON mode."""
        cfg = config or self.get_default_config()

        system_prompt = (
            "You are a helpful assistant that extracts information "
            "and returns valid JSON."
        )
        if schema_hint:
            system_prompt += f"\n\nExpected JSON schema:\n{schema_hint}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        payload = {
            "model": cfg.model,
            "messages": messages,
            "temperature": 0.1,  # Low temperature for extraction
            "max_tokens": cfg.max_tokens,
            "response_format": {"type": "json_object"},
        }

        try:
            response = await self.client.post(
                OPENAI_API_URL,
                json=payload,
                timeout=cfg.timeout_seconds,
            )
        except httpx.TimeoutException:
            raise ProviderTimeoutError(self.provider_name, cfg.timeout_seconds)

        if response.status_code == 401:
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
        content = data["choices"][0]["message"]["content"]

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from OpenAI: {e}")
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
        """Extract structured JSON using OpenAI JSON mode with token tracking."""
        cfg = config or self.get_default_config()

        system_prompt = (
            "You are a helpful assistant that extracts information "
            "and returns valid JSON."
        )
        if schema_hint:
            system_prompt += f"\n\nExpected JSON schema:\n{schema_hint}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        payload = {
            "model": cfg.model,
            "messages": messages,
            "temperature": 0.1,  # Low temperature for extraction
            "max_tokens": cfg.max_tokens,
            "response_format": {"type": "json_object"},
        }

        try:
            response = await self.client.post(
                OPENAI_API_URL,
                json=payload,
                timeout=cfg.timeout_seconds,
            )
        except httpx.TimeoutException:
            raise ProviderTimeoutError(self.provider_name, cfg.timeout_seconds)

        if response.status_code == 401:
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
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})

        try:
            parsed_data = json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from OpenAI: {e}")
            raise ProviderResponseError(
                self.provider_name,
                200,
                f"Invalid JSON response: {content[:200]}",
            )

        return LLMJsonResponse(
            data=parsed_data,
            model=data["model"],
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        )

    def get_default_model(self) -> str:
        """Get default OpenAI model."""
        return self._default_model

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
