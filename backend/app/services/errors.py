"""Custom errors for provider services."""


class ProviderError(Exception):
    """Base exception for all provider-related errors."""

    def __init__(self, message: str, provider: str | None = None):
        self.message = message
        self.provider = provider
        super().__init__(message)


class ConfigMissingError(ProviderError):
    """Raised when a required API key is not configured."""

    def __init__(self, provider: str):
        super().__init__(
            f"API key for {provider} is not configured. Please set up the key in Admin settings.",
            provider=provider,
        )


class ProviderAuthError(ProviderError):
    """Raised when authentication with provider fails (invalid key)."""

    def __init__(self, provider: str, details: str | None = None):
        msg = f"Authentication failed for {provider}"
        if details:
            msg += f": {details}"
        super().__init__(msg, provider=provider)


class ProviderRateLimitError(ProviderError):
    """Raised when provider rate limit is exceeded."""

    def __init__(self, provider: str, retry_after: int | None = None):
        msg = f"Rate limit exceeded for {provider}"
        if retry_after:
            msg += f". Retry after {retry_after} seconds"
        self.retry_after = retry_after
        super().__init__(msg, provider=provider)


class ProviderTimeoutError(ProviderError):
    """Raised when provider request times out."""

    def __init__(self, provider: str, timeout_seconds: float):
        super().__init__(
            f"Request to {provider} timed out after {timeout_seconds}s",
            provider=provider,
        )


class ProviderResponseError(ProviderError):
    """Raised when provider returns an unexpected response."""

    def __init__(self, provider: str, status_code: int, details: str | None = None):
        msg = f"{provider} returned error status {status_code}"
        if details:
            msg += f": {details}"
        self.status_code = status_code
        super().__init__(msg, provider=provider)


class ProviderTokenLimitError(ProviderError):
    """Raised when provider output is truncated due to token limit (MAX_TOKENS)."""

    def __init__(self, provider: str, details: str | None = None):
        msg = f"{provider} output was truncated due to token limit"
        if details:
            msg += f": {details}"
        super().__init__(msg, provider=provider)

