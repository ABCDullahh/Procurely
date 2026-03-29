"""Admin API Key endpoints - CRUD with encrypted storage."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status

from app.api.deps import AdminUser, DbSession
from app.core.security import decrypt_api_key, encrypt_api_key, mask_api_key
from app.models.api_key import ApiKey, ApiKeyProvider
from app.models.audit_log import AuditAction
from app.schemas.api_key import (
    ApiKeyListResponse,
    ApiKeyResponse,
    ApiKeySetRequest,
    ApiKeyTestResponse,
    ProviderModel,
    ProviderModelsResponse,
)
from app.services.audit import log_audit
from app.services.provider_tests import test_provider_key

router = APIRouter(prefix="/api-keys", tags=["admin-api-keys"])


def _api_key_to_response(key: ApiKey) -> ApiKeyResponse:
    """Convert ApiKey model to response schema."""
    return ApiKeyResponse(
        provider=key.provider,
        masked_tail=f"****{key.masked_tail}",
        is_active=key.is_active,
        default_model=key.default_model,
        updated_at=key.updated_at,
        updated_by_email=key.updated_by.email,
    )


@router.get("", response_model=ApiKeyListResponse)
def list_api_keys(db: DbSession, current_user: AdminUser) -> ApiKeyListResponse:
    """List all configured API keys (masked values only)."""
    keys = db.query(ApiKey).filter(ApiKey.is_active == True).all()  # noqa: E712

    return ApiKeyListResponse(
        keys=[_api_key_to_response(key) for key in keys]
    )


@router.get("/{provider}", response_model=ApiKeyResponse)
def get_api_key(
    provider: ApiKeyProvider,
    db: DbSession,
    current_user: AdminUser,
) -> ApiKeyResponse:
    """Get a specific API key (masked value only)."""
    key = (
        db.query(ApiKey)
        .filter(ApiKey.provider == provider.value, ApiKey.is_active == True)  # noqa: E712
        .first()
    )
    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key for provider {provider.value} not found",
        )
    return _api_key_to_response(key)


@router.put("/{provider}", response_model=ApiKeyResponse)
def set_api_key(
    provider: ApiKeyProvider,
    request: ApiKeySetRequest,
    db: DbSession,
    current_user: AdminUser,
) -> ApiKeyResponse:
    """Set or update an API key for a provider."""
    raw_value = request.value

    # Encrypt the key
    encrypted = encrypt_api_key(raw_value)
    masked_tail = mask_api_key(raw_value, visible_chars=4).replace("*", "")[-4:]

    # Check for existing key
    existing = (
        db.query(ApiKey)
        .filter(ApiKey.provider == provider.value)
        .first()
    )

    if existing:
        # Update existing key
        existing.encrypted_value = encrypted
        existing.masked_tail = masked_tail
        existing.is_active = True
        existing.default_model = request.default_model
        existing.updated_by_user_id = current_user.id
        db.commit()
        db.refresh(existing)
        key = existing
    else:
        # Create new key
        key = ApiKey(
            provider=provider.value,
            encrypted_value=encrypted,
            masked_tail=masked_tail,
            is_active=True,
            default_model=request.default_model,
            updated_by_user_id=current_user.id,
        )
        db.add(key)
        db.commit()
        db.refresh(key)

    # Audit log
    log_audit(
        db=db,
        actor_user_id=current_user.id,
        action=AuditAction.API_KEY_SET,
        target_type="api_key",
        target_id=provider.value,
        metadata={"provider": provider.value},
    )

    return _api_key_to_response(key)


@router.post("/{provider}/rotate", response_model=ApiKeyResponse)
def rotate_api_key(
    provider: ApiKeyProvider,
    request: ApiKeySetRequest,
    db: DbSession,
    current_user: AdminUser,
) -> ApiKeyResponse:
    """Rotate an API key (deactivates old, sets new)."""
    # Deactivate existing key
    existing = (
        db.query(ApiKey)
        .filter(ApiKey.provider == provider.value, ApiKey.is_active == True)  # noqa: E712
        .first()
    )

    if existing:
        existing.is_active = False
        db.commit()

    # Create new key
    raw_value = request.value
    encrypted = encrypt_api_key(raw_value)
    masked_tail = mask_api_key(raw_value, visible_chars=4).replace("*", "")[-4:]

    new_key = ApiKey(
        provider=provider.value,
        encrypted_value=encrypted,
        masked_tail=masked_tail,
        is_active=True,
        default_model=request.default_model,
        updated_by_user_id=current_user.id,
    )
    db.add(new_key)
    db.commit()
    db.refresh(new_key)

    # Audit log
    log_audit(
        db=db,
        actor_user_id=current_user.id,
        action=AuditAction.API_KEY_ROTATE,
        target_type="api_key",
        target_id=provider.value,
        metadata={"provider": provider.value},
    )

    return _api_key_to_response(new_key)


@router.delete("/{provider}", status_code=status.HTTP_204_NO_CONTENT)
def delete_api_key(
    provider: ApiKeyProvider,
    db: DbSession,
    current_user: AdminUser,
) -> None:
    """Delete (deactivate) an API key.

    Also disables any data providers that depend on this API key.
    """
    from app.models.data_provider import DataProvider

    existing = (
        db.query(ApiKey)
        .filter(ApiKey.provider == provider.value, ApiKey.is_active == True)  # noqa: E712
        .first()
    )

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key for provider {provider.value} not found",
        )

    existing.is_active = False

    # Disable any data providers that depend on this API key
    affected_providers = (
        db.query(DataProvider)
        .filter(
            DataProvider.api_key_provider == provider.value,
            DataProvider.is_enabled == True,  # noqa: E712
        )
        .all()
    )

    disabled_providers = []
    for dp in affected_providers:
        dp.is_enabled = False
        dp.is_default = False  # Can't be default if not enabled
        disabled_providers.append(dp.name)

    db.commit()

    # Audit log
    log_audit(
        db=db,
        actor_user_id=current_user.id,
        action=AuditAction.API_KEY_DELETE,
        target_type="api_key",
        target_id=provider.value,
        metadata={
            "provider": provider.value,
            "disabled_providers": disabled_providers,
        },
    )


@router.post("/{provider}/test", response_model=ApiKeyTestResponse)
async def test_api_key(
    provider: ApiKeyProvider,
    db: DbSession,
    current_user: AdminUser,
) -> ApiKeyTestResponse:
    """Test an API key by making a lightweight request to the provider.

    This validates the key is correctly configured and has access.
    """
    # Get decrypted key
    key = (
        db.query(ApiKey)
        .filter(ApiKey.provider == provider.value, ApiKey.is_active == True)  # noqa: E712
        .first()
    )

    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key for provider {provider.value} not found",
        )

    decrypted_key = decrypt_api_key(key.encrypted_value)

    # Test the key
    result = await test_provider_key(provider.value, decrypted_key)

    # Audit log
    log_audit(
        db=db,
        actor_user_id=current_user.id,
        action=AuditAction.API_KEY_TEST,
        target_type="api_key",
        target_id=provider.value,
        metadata={
            "provider": provider.value,
            "success": result.ok,
            "message": result.message,
        },
    )

    return result


def get_decrypted_key(db: DbSession, provider: str) -> str | None:
    """Get decrypted API key for internal server use only.

    This is used by provider test endpoints and pipeline services.
    NEVER expose this in any API response.
    """
    key = (
        db.query(ApiKey)
        .filter(ApiKey.provider == provider, ApiKey.is_active == True)  # noqa: E712
        .first()
    )
    if not key:
        return None
    return decrypt_api_key(key.encrypted_value)


def get_api_key_with_model(db: DbSession, provider: str) -> tuple[str | None, str | None]:
    """Get decrypted API key and default model for internal server use.

    Returns:
        Tuple of (decrypted_key, default_model) or (None, None) if not found.
    """
    key = (
        db.query(ApiKey)
        .filter(ApiKey.provider == provider, ApiKey.is_active == True)  # noqa: E712
        .first()
    )
    if not key:
        return None, None
    return decrypt_api_key(key.encrypted_value), key.default_model


# Curated model lists for providers
OPENAI_MODELS = [
    ProviderModel(id="gpt-4o", label="GPT-4o (Recommended)", supports=["text", "json"]),
    ProviderModel(id="gpt-4o-mini", label="GPT-4o Mini (Fast)", supports=["text", "json"]),
    ProviderModel(id="gpt-4-turbo", label="GPT-4 Turbo", supports=["text", "json"]),
    ProviderModel(id="gpt-3.5-turbo", label="GPT-3.5 Turbo", supports=["text", "json"]),
]

GEMINI_MODELS = [
    ProviderModel(
        id="gemini-1.5-pro", label="Gemini 1.5 Pro", supports=["text", "json"]
    ),
    ProviderModel(
        id="gemini-1.5-flash", label="Gemini 1.5 Flash", supports=["text", "json"]
    ),
    ProviderModel(id="gemini-pro", label="Gemini Pro", supports=["text", "json"]),
]


@router.get("/provider-models/{provider}", response_model=ProviderModelsResponse)
async def get_provider_models(
    provider: ApiKeyProvider,
    db: DbSession,
    current_user: AdminUser,
) -> ProviderModelsResponse:
    """Get available models for a provider.

    Tries live fetching from provider API first.
    Falls back to curated list if live fetch fails.
    """
    from app.services.provider_models import (
        fetch_gemini_models_live,
        fetch_openai_models_live,
        get_cache_timestamp,
    )

    # Check if key exists
    key = (
        db.query(ApiKey)
        .filter(ApiKey.provider == provider.value, ApiKey.is_active == True)  # noqa: E712
        .first()
    )

    if not key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Configure API key for {provider.value} first",
        )

    decrypted_key = decrypt_api_key(key.encrypted_value)
    models: list[ProviderModel] = []
    source = "live"

    # Try live fetching first
    if provider == ApiKeyProvider.GEMINI:
        live_models = await fetch_gemini_models_live(decrypted_key)
        if live_models:
            models = live_models
            cache_ts = get_cache_timestamp("GEMINI")
            fetched_at = cache_ts or datetime.now(timezone.utc)
        else:
            # Fallback to curated
            models = GEMINI_MODELS
            source = "curated"
            fetched_at = datetime.now(timezone.utc)

    elif provider == ApiKeyProvider.OPENAI:
        live_models = await fetch_openai_models_live(decrypted_key)
        if live_models:
            models = live_models
            cache_ts = get_cache_timestamp("OPENAI")
            fetched_at = cache_ts or datetime.now(timezone.utc)
        else:
            # Fallback to curated
            models = OPENAI_MODELS
            source = "curated"
            fetched_at = datetime.now(timezone.utc)
    else:
        models = []
        fetched_at = datetime.now(timezone.utc)

    return ProviderModelsResponse(
        provider=provider.value,
        models=models,
        source=source,
        fetched_at=fetched_at,
    )


