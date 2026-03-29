"""API key access service."""

from sqlalchemy.orm import Session

from app.core.security import decrypt_api_key
from app.models.api_key import ApiKey
from app.services.errors import ConfigMissingError


def get_active_api_key(db: Session, provider: str) -> str:
    """
    Get the decrypted active API key for a provider.

    Args:
        db: Database session
        provider: Provider name (OPENAI, GEMINI, SEARCH_PROVIDER)

    Returns:
        Decrypted API key string

    Raises:
        ConfigMissingError: If no active key exists for the provider
    """
    key = (
        db.query(ApiKey)
        .filter(
            ApiKey.provider == provider,
            ApiKey.is_active == True,  # noqa: E712
        )
        .first()
    )

    if not key:
        raise ConfigMissingError(provider)

    return decrypt_api_key(key.encrypted_value)


def get_active_api_key_with_model(db: Session, provider: str) -> tuple[str, str | None]:
    """
    Get the decrypted active API key and default model for a provider.

    Args:
        db: Database session
        provider: Provider name (OPENAI, GEMINI, SEARCH_PROVIDER)

    Returns:
        Tuple of (decrypted API key, default_model or None)

    Raises:
        ConfigMissingError: If no active key exists for the provider
    """
    key = (
        db.query(ApiKey)
        .filter(
            ApiKey.provider == provider,
            ApiKey.is_active == True,  # noqa: E712
        )
        .first()
    )

    if not key:
        raise ConfigMissingError(provider)

    return decrypt_api_key(key.encrypted_value), key.default_model

