"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class LLMResponse:
    """Standardized LLM response."""

    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class LLMJsonResponse:
    """Standardized LLM JSON extraction response with token tracking."""

    data: dict[str, Any]
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class LLMConfig:
    """Configuration for LLM requests."""

    model: str
    temperature: float = 0.7
    max_tokens: int = 100000  # High limit for thinking models like gemini-2.5-pro
    timeout_seconds: float = 180.0  # Longer timeout for complex operations


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    provider_name: str = "base"

    @abstractmethod
    async def complete_text(
        self,
        prompt: str,
        config: LLMConfig | None = None,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """
        Generate text completion.

        Args:
            prompt: User prompt text
            config: LLM configuration (model, temperature, etc.)
            system_prompt: Optional system prompt

        Returns:
            LLMResponse with generated content

        Raises:
            ProviderAuthError: Invalid API key
            ProviderRateLimitError: Rate limit exceeded
            ProviderTimeoutError: Request timed out
            ProviderResponseError: Unexpected response
        """
        pass

    @abstractmethod
    async def extract_json(
        self,
        prompt: str,
        schema_hint: str | None = None,
        config: LLMConfig | None = None,
    ) -> dict[str, Any]:
        """
        Extract structured JSON from prompt.

        Args:
            prompt: Prompt requesting JSON output
            schema_hint: Optional JSON schema hint for the model
            config: LLM configuration

        Returns:
            Parsed JSON dict

        Raises:
            ProviderError: If JSON parsing fails
            ProviderAuthError: Invalid API key
        """
        pass

    @abstractmethod
    async def extract_json_with_tokens(
        self,
        prompt: str,
        schema_hint: str | None = None,
        config: LLMConfig | None = None,
    ) -> LLMJsonResponse:
        """
        Extract structured JSON from prompt with token usage tracking.

        Args:
            prompt: Prompt requesting JSON output
            schema_hint: Optional JSON schema hint for the model
            config: LLM configuration

        Returns:
            LLMJsonResponse with parsed JSON and token counts

        Raises:
            ProviderError: If JSON parsing fails
            ProviderAuthError: Invalid API key
        """
        pass

    def get_default_config(self) -> LLMConfig:
        """Get default configuration for this provider."""
        return LLMConfig(model=self.get_default_model())

    @abstractmethod
    def get_default_model(self) -> str:
        """Get default model name for this provider."""
        pass
