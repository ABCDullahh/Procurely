"""Data Providers API - list and check status of search/scrape providers."""

import json
import logging

from fastapi import APIRouter, HTTPException, status

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.core.redis import cache_get, cache_set
from app.models.api_key import ApiKey
from app.models.app_settings import AppSettings
from app.models.data_provider import DEFAULT_PROVIDERS, DataProvider
from app.schemas.providers import (
    DataProviderResponse,
    ProvidersListResponse,
    ProviderStatusResponse,
    UpdateProviderRequest,
)
from app.schemas.research import ResearchConfig, ResearchConfigUpdate
from app.services.providers.registry import _scrape_providers, _search_providers

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/providers", tags=["providers"])


def _get_configured_api_keys(db: DbSession) -> set[str]:
    """Get set of provider names that have configured API keys."""
    keys = (
        db.query(ApiKey.provider)
        .filter(ApiKey.is_active == True)  # noqa: E712
        .all()
    )
    return {key[0] for key in keys}


def _provider_to_response(
    provider_data: dict,
    configured_keys: set[str],
) -> DataProviderResponse:
    """Convert provider dict to response schema."""
    requires_key = provider_data.get("requires_api_key", False)
    api_key_provider = provider_data.get("api_key_provider")

    # Check if configured
    is_configured = True
    if requires_key and api_key_provider:
        is_configured = api_key_provider in configured_keys

    return DataProviderResponse(
        name=provider_data["name"],
        provider_type=provider_data["provider_type"],
        display_name=provider_data["display_name"],
        description=provider_data.get("description"),
        requires_api_key=requires_key,
        api_key_provider=api_key_provider,
        is_configured=is_configured,
        is_enabled=provider_data.get("is_enabled", True),
        is_default=provider_data.get("is_default", False),
        is_free=provider_data.get("is_free", False),
    )


@router.get("", response_model=ProvidersListResponse)
def list_providers(
    db: DbSession,
    current_user: CurrentUser,
) -> ProvidersListResponse:
    """
    List all available data providers.

    Returns both search and scrape providers with their configuration status.
    """
    # Check cache first (TTL 10 minutes)
    cache_key = "providers:list"
    cached = cache_get(cache_key)
    if cached:
        return ProvidersListResponse(**cached)

    configured_keys = _get_configured_api_keys(db)

    # First try to get from database
    db_providers = db.query(DataProvider).all()

    if db_providers:
        # Use database providers
        providers = [
            DataProviderResponse(
                name=p.name,
                provider_type=p.provider_type,
                display_name=p.display_name,
                description=p.description,
                requires_api_key=p.requires_api_key,
                api_key_provider=p.api_key_provider,
                is_configured=(
                    p.api_key_provider in configured_keys
                    if p.requires_api_key and p.api_key_provider
                    else True
                ),
                is_enabled=p.is_enabled,
                is_default=p.is_default,
                is_free=p.is_free,
            )
            for p in db_providers
        ]
    else:
        # Fallback to DEFAULT_PROVIDERS constant
        providers = [
            _provider_to_response(p, configured_keys)
            for p in DEFAULT_PROVIDERS
        ]

    # Get registered provider names from registry
    search_names = list(_search_providers.keys())
    scrape_names = list(_scrape_providers.keys())

    response = ProvidersListResponse(
        providers=providers,
        search_providers=search_names,
        scrape_providers=scrape_names,
    )

    # Cache for 10 minutes (600 seconds)
    cache_set(cache_key, response.model_dump(), ttl=600)

    return response


@router.get("/defaults")
def get_default_providers(
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """
    Get default provider selection.

    Returns the default providers to pre-select in the UI.
    Reads from database if seeded, otherwise falls back to constants.
    """
    configured_keys = _get_configured_api_keys(db)
    default_search = []
    default_scrape = []

    # Try database first
    db_providers = db.query(DataProvider).filter(
        DataProvider.is_default == True,  # noqa: E712
        DataProvider.is_enabled == True,  # noqa: E712
    ).all()

    if db_providers:
        for p in db_providers:
            # Check if usable (has key if needed)
            is_usable = True
            if p.requires_api_key and p.api_key_provider:
                is_usable = p.api_key_provider in configured_keys

            if is_usable:
                if p.provider_type == "SEARCH":
                    default_search.append(p.name)
                elif p.provider_type == "SCRAPE":
                    default_scrape.append(p.name)
    else:
        # Fallback to DEFAULT_PROVIDERS constant
        for provider in DEFAULT_PROVIDERS:
            is_default = provider.get("is_default", False)
            requires_key = provider.get("requires_api_key", False)
            api_key_provider = provider.get("api_key_provider")

            is_usable = True
            if requires_key and api_key_provider:
                is_usable = api_key_provider in configured_keys

            if is_default and is_usable:
                provider_type = provider["provider_type"]
                if provider_type == "SEARCH":
                    default_search.append(provider["name"])
                elif provider_type == "SCRAPE":
                    default_scrape.append(provider["name"])

    return {
        "search": default_search or ["SERPER"],
        "scrape": default_scrape or ["JINA_READER"],
    }


@router.get("/{provider_name}/status", response_model=ProviderStatusResponse)
async def check_provider_status(
    provider_name: str,
    db: DbSession,
    current_user: CurrentUser,
) -> ProviderStatusResponse:
    """
    Check if a specific provider is available and configured.

    This does NOT test the actual connection - just checks configuration.
    """
    configured_keys = _get_configured_api_keys(db)

    # Find provider info
    provider_info = None
    for p in DEFAULT_PROVIDERS:
        if p["name"] == provider_name:
            provider_info = p
            break

    if not provider_info:
        return ProviderStatusResponse(
            provider=provider_name,
            status="UNKNOWN",
            message=f"Provider '{provider_name}' not found",
        )

    requires_key = provider_info.get("requires_api_key", False)
    api_key_provider = provider_info.get("api_key_provider")

    # Check if configured
    if requires_key and api_key_provider:
        if api_key_provider not in configured_keys:
            return ProviderStatusResponse(
                provider=provider_name,
                status="NOT_CONFIGURED",
                message=f"API key for {api_key_provider} not configured",
            )

    # Check if provider is registered
    is_registered = (
        provider_name in _search_providers or provider_name in _scrape_providers
    )

    if not is_registered:
        return ProviderStatusResponse(
            provider=provider_name,
            status="UNAVAILABLE",
            message="Provider not registered in system",
        )

    return ProviderStatusResponse(
        provider=provider_name,
        status="AVAILABLE",
        message="Provider is configured and available",
    )


@router.put("/{provider_name}", response_model=DataProviderResponse)
def update_provider(
    provider_name: str,
    request: UpdateProviderRequest,
    db: DbSession,
    admin_user: AdminUser,
) -> DataProviderResponse:
    """
    Update provider settings (enable/disable, set default).

    Requires admin role.

    Validation rules:
    - Cannot set as default if not enabled
    - Cannot enable if requires_api_key and key not configured
    - Disabling auto-unsets is_default
    """
    # Get provider from database
    provider = db.query(DataProvider).filter(DataProvider.name == provider_name).first()

    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{provider_name}' not found",
        )

    configured_keys = _get_configured_api_keys(db)

    # Handle is_enabled change
    if request.is_enabled is not None:
        if request.is_enabled:
            # Enabling: check if API key is configured
            if provider.requires_api_key and provider.api_key_provider:
                if provider.api_key_provider not in configured_keys:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Cannot enable {provider.display_name}: API key not configured",
                    )
        else:
            # Disabling: auto-unset default
            provider.is_default = False

        provider.is_enabled = request.is_enabled

    # Handle is_default change
    if request.is_default is not None:
        if request.is_default:
            # Setting as default: must be enabled
            if not provider.is_enabled:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot set {provider.display_name} as default: provider is disabled",
                )
            # Must have API key if required
            if provider.requires_api_key and provider.api_key_provider:
                if provider.api_key_provider not in configured_keys:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Cannot set {provider.display_name} as default: API key not configured",
                    )

        provider.is_default = request.is_default

    db.commit()
    db.refresh(provider)

    # Check if configured for response
    is_configured = True
    if provider.requires_api_key and provider.api_key_provider:
        is_configured = provider.api_key_provider in configured_keys

    return DataProviderResponse(
        name=provider.name,
        provider_type=provider.provider_type,
        display_name=provider.display_name,
        description=provider.description,
        requires_api_key=provider.requires_api_key,
        api_key_provider=provider.api_key_provider,
        is_configured=is_configured,
        is_enabled=provider.is_enabled,
        is_default=provider.is_default,
        is_free=provider.is_free,
    )


@router.get("/shopping/status")
def get_shopping_provider_status(
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """
    Check if Google Shopping integration (via SerpAPI) is configured.

    Returns the status of SerpAPI configuration for shopping searches.
    """
    configured_keys = _get_configured_api_keys(db)
    is_configured = "SERPAPI" in configured_keys

    # Check if SERPAPI_SHOPPING provider is enabled
    shopping_provider = db.query(DataProvider).filter(
        DataProvider.name == "SERPAPI_SHOPPING"
    ).first()

    is_enabled = shopping_provider.is_enabled if shopping_provider else False

    return {
        "provider": "SERPAPI_SHOPPING",
        "is_configured": is_configured,
        "is_enabled": is_enabled,
        "message": (
            "Shopping integration ready"
            if is_configured and is_enabled
            else "Configure SERPAPI key in Admin → API Keys to enable shopping"
        ),
    }


@router.get("/research-config", response_model=ResearchConfig)
def get_research_config(
    db: DbSession,
    current_user: CurrentUser,
) -> ResearchConfig:
    """
    Get current DeepResearch configuration.

    Returns the default research configuration settings.
    """
    # Try to get from app settings
    setting = db.query(AppSettings).filter(
        AppSettings.key == "research.config"
    ).first()

    if setting and setting.value:
        try:
            config_data = json.loads(setting.value)
            return ResearchConfig(**config_data)
        except (json.JSONDecodeError, TypeError):
            pass

    # Return defaults
    return ResearchConfig()


@router.put("/research-config", response_model=ResearchConfig)
def update_research_config(
    config: ResearchConfigUpdate,
    db: DbSession,
    admin_user: AdminUser,
) -> ResearchConfig:
    """
    Update DeepResearch configuration.

    Requires admin role.
    """
    # Get current config
    setting = db.query(AppSettings).filter(
        AppSettings.key == "research.config"
    ).first()

    current_config = ResearchConfig()
    if setting and setting.value:
        try:
            current_data = json.loads(setting.value)
            current_config = ResearchConfig(**current_data)
        except (json.JSONDecodeError, TypeError):
            pass

    # Apply updates
    update_data = config.model_dump(exclude_unset=True)
    new_data = current_config.model_dump()
    for key, value in update_data.items():
        if value is not None:
            new_data[key] = value

    new_config = ResearchConfig(**new_data)

    # Save to database
    if setting:
        setting.value = json.dumps(new_config.model_dump())
    else:
        setting = AppSettings(
            key="research.config",
            value=json.dumps(new_config.model_dump()),
        )
        db.add(setting)

    db.commit()

    logger.info(f"Research config updated by {admin_user.email}: {new_config}")
    return new_config


@router.get("/locales")
def get_available_locales(
    current_user: CurrentUser,
) -> dict:
    """
    Get available locales for region-focused search.

    Returns list of supported locales with display names.
    """
    return {
        "locales": [
            {"code": "id_ID", "name": "Indonesia", "country_code": "ID", "default": True},
            {"code": "en_US", "name": "United States", "country_code": "US", "default": False},
            {"code": "en_GB", "name": "United Kingdom", "country_code": "GB", "default": False},
            {"code": "en_SG", "name": "Singapore", "country_code": "SG", "default": False},
            {"code": "en_AU", "name": "Australia", "country_code": "AU", "default": False},
            {"code": "ja_JP", "name": "Japan", "country_code": "JP", "default": False},
            {"code": "zh_CN", "name": "China", "country_code": "CN", "default": False},
            {"code": "de_DE", "name": "Germany", "country_code": "DE", "default": False},
        ],
        "default": "id_ID",
    }
