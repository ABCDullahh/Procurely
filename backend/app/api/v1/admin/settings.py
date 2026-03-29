"""Admin Settings API endpoints for application configuration."""

from enum import Enum
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.deps import AdminUser, DbSession
from app.models import ApiKey, AppSettings


class SearchStrategy(str, Enum):
    """Supported search strategies."""
    SERPER = "SERPER"
    GEMINI_GROUNDING = "GEMINI_GROUNDING"
    TAVILY = "TAVILY"


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "OPENAI"
    GEMINI = "GEMINI"


# --- Web Search Config ---
class WebSearchConfig(BaseModel):
    """Web search configuration."""
    provider: SearchStrategy = SearchStrategy.SERPER
    gemini_model: Optional[str] = None  # Required if provider is GEMINI_GROUNDING
    key_configured: bool = False


# --- LLM Config ---
class LLMConfig(BaseModel):
    """LLM provider + model configuration."""
    provider: LLMProvider = LLMProvider.OPENAI
    model: str = ""
    key_configured: bool = False


# --- AI Config Response/Request ---
class AIConfigResponse(BaseModel):
    """Complete AI configuration response."""
    web_search: WebSearchConfig
    procurement_llm: LLMConfig
    copilot_llm: LLMConfig
    ai_search_llm: LLMConfig  # For AI Search chat feature
    available_search_providers: list[dict] = [
        {
            "value": "SERPER",
            "label": "Serper (Google Search)",
            "requires_key": "SEARCH_PROVIDER"
        },
        {
            "value": "TAVILY",
            "label": "Tavily AI Search",
            "requires_key": "TAVILY"
        },
        {
            "value": "GEMINI_GROUNDING",
            "label": "Gemini Grounding",
            "requires_key": "GEMINI"
        },
    ]


class AIConfigRequest(BaseModel):
    """Request to update AI configuration."""
    web_search_provider: Optional[SearchStrategy] = None
    web_search_gemini_model: Optional[str] = None
    procurement_provider: Optional[LLMProvider] = None
    procurement_model: Optional[str] = None
    copilot_provider: Optional[LLMProvider] = None
    copilot_model: Optional[str] = None
    ai_search_provider: Optional[LLMProvider] = None
    ai_search_model: Optional[str] = None


# --- Legacy Search Strategy for backward compatibility ---
class SearchStrategyResponse(BaseModel):
    """Response for search strategy setting."""
    strategy: SearchStrategy
    description: str = "Web search provider used by the pipeline"
    available_strategies: list[dict] = [
        {
            "value": "SERPER",
            "label": "Serper (Google Search)",
            "description": "Uses Serper.dev API for Google search results"
        },
        {
            "value": "TAVILY",
            "label": "Tavily AI Search",
            "description": "Uses Tavily AI search API optimized for RAG"
        },
        {
            "value": "GEMINI_GROUNDING",
            "label": "Gemini Grounding",
            "description": "Uses Google Gemini's built-in web grounding"
        },
    ]


class SearchStrategyRequest(BaseModel):
    """Request to update search strategy."""
    strategy: SearchStrategy


router = APIRouter(prefix="/settings", tags=["admin-settings"])


# --- Helper functions ---
def _get_setting(db: DbSession, key: str, default: str = "") -> str:
    """Get a setting value from app_settings."""
    setting = db.query(AppSettings).filter(AppSettings.key == key).first()
    return setting.value if setting else default


def _set_setting(db: DbSession, key: str, value: str, desc: str = "") -> None:
    """Set a setting value in app_settings."""
    setting = db.query(AppSettings).filter(AppSettings.key == key).first()
    if setting:
        setting.value = value
    else:
        setting = AppSettings(key=key, value=value, description=desc)
        db.add(setting)


def _is_key_configured(db: DbSession, provider: str) -> bool:
    """Check if an API key is configured for a provider."""
    key = (
        db.query(ApiKey)
        .filter(ApiKey.provider == provider, ApiKey.is_active)
        .first()
    )
    return key is not None


# --- AI Config Endpoints ---
@router.get("/ai-config", response_model=AIConfigResponse)
def get_ai_config(
    db: DbSession,
    _admin: AdminUser,
) -> AIConfigResponse:
    """Get complete AI configuration including validation status."""
    # Web search config
    ws_provider_str = _get_setting(db, "web_search.provider", "SERPER")
    try:
        ws_provider = SearchStrategy(ws_provider_str)
    except ValueError:
        ws_provider = SearchStrategy.SERPER

    ws_gemini_model = _get_setting(db, "web_search.gemini_model", "")

    # Determine key configured for web search
    if ws_provider == SearchStrategy.SERPER:
        ws_key_ok = _is_key_configured(db, "SEARCH_PROVIDER")
    elif ws_provider == SearchStrategy.TAVILY:
        ws_key_ok = _is_key_configured(db, "TAVILY")
    else:  # GEMINI_GROUNDING
        ws_key_ok = _is_key_configured(db, "GEMINI")

    # Procurement LLM config
    proc_provider_str = _get_setting(db, "llm.procurement.provider", "OPENAI")
    try:
        proc_provider = LLMProvider(proc_provider_str)
    except ValueError:
        proc_provider = LLMProvider.OPENAI

    proc_model = _get_setting(db, "llm.procurement.model", "")
    proc_key_ok = _is_key_configured(db, proc_provider.value)

    # Copilot LLM config
    cop_provider_str = _get_setting(db, "llm.copilot.provider", "GEMINI")
    try:
        cop_provider = LLMProvider(cop_provider_str)
    except ValueError:
        cop_provider = LLMProvider.GEMINI

    cop_model = _get_setting(db, "llm.copilot.model", "")
    cop_key_ok = _is_key_configured(db, cop_provider.value)

    # AI Search LLM config
    ais_provider_str = _get_setting(db, "llm.ai_search.provider", "OPENAI")
    try:
        ais_provider = LLMProvider(ais_provider_str)
    except ValueError:
        ais_provider = LLMProvider.OPENAI

    ais_model = _get_setting(db, "llm.ai_search.model", "gpt-4o-mini")
    ais_key_ok = _is_key_configured(db, ais_provider.value)

    return AIConfigResponse(
        web_search=WebSearchConfig(
            provider=ws_provider,
            gemini_model=ws_gemini_model or None,
            key_configured=ws_key_ok,
        ),
        procurement_llm=LLMConfig(
            provider=proc_provider,
            model=proc_model,
            key_configured=proc_key_ok,
        ),
        copilot_llm=LLMConfig(
            provider=cop_provider,
            model=cop_model,
            key_configured=cop_key_ok,
        ),
        ai_search_llm=LLMConfig(
            provider=ais_provider,
            model=ais_model,
            key_configured=ais_key_ok,
        ),
    )


@router.put("/ai-config", response_model=AIConfigResponse)
def set_ai_config(
    db: DbSession,
    _admin: AdminUser,
    request: AIConfigRequest,
) -> AIConfigResponse:
    """Update AI configuration.

    Validates that required API keys are configured before saving.
    """
    # Web search
    if request.web_search_provider is not None:
        # Validate key exists
        if request.web_search_provider == SearchStrategy.SERPER:
            if not _is_key_configured(db, "SEARCH_PROVIDER"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Serper requires SEARCH_PROVIDER API key. "
                           "Configure it in Admin → API Keys first.",
                )
        elif request.web_search_provider == SearchStrategy.TAVILY:
            if not _is_key_configured(db, "TAVILY"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tavily requires TAVILY API key. "
                           "Configure it in Admin → API Keys first.",
                )
        elif request.web_search_provider == SearchStrategy.GEMINI_GROUNDING:
            if not _is_key_configured(db, "GEMINI"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Gemini Grounding requires GEMINI API key. "
                           "Configure it in Admin → API Keys first.",
                )

        _set_setting(
            db, "web_search.provider",
            request.web_search_provider.value,
            "Web search provider"
        )
        # Also update legacy key for backward compat
        _set_setting(
            db, "search_strategy",
            request.web_search_provider.value,
            "Web search provider (legacy)"
        )

    if request.web_search_gemini_model is not None:
        _set_setting(
            db, "web_search.gemini_model",
            request.web_search_gemini_model,
            "Gemini model for grounding"
        )

    # Procurement LLM
    if request.procurement_provider is not None:
        if not _is_key_configured(db, request.procurement_provider.value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{request.procurement_provider.value} API key not configured. "
                       f"Configure it in Admin → API Keys first.",
            )
        _set_setting(
            db, "llm.procurement.provider",
            request.procurement_provider.value,
            "LLM provider for procurement pipeline"
        )

    if request.procurement_model is not None:
        _set_setting(
            db, "llm.procurement.model",
            request.procurement_model,
            "LLM model for procurement pipeline"
        )

    # Copilot LLM
    if request.copilot_provider is not None:
        if not _is_key_configured(db, request.copilot_provider.value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{request.copilot_provider.value} API key not configured. "
                       f"Configure it in Admin → API Keys first.",
            )
        _set_setting(
            db, "llm.copilot.provider",
            request.copilot_provider.value,
            "LLM provider for Copilot"
        )

    if request.copilot_model is not None:
        _set_setting(
            db, "llm.copilot.model",
            request.copilot_model,
            "LLM model for Copilot"
        )

    # AI Search LLM
    if request.ai_search_provider is not None:
        if not _is_key_configured(db, request.ai_search_provider.value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{request.ai_search_provider.value} API key not configured. "
                       f"Configure it in Admin → API Keys first.",
            )
        _set_setting(
            db, "llm.ai_search.provider",
            request.ai_search_provider.value,
            "LLM provider for AI Search chat"
        )

    if request.ai_search_model is not None:
        _set_setting(
            db, "llm.ai_search.model",
            request.ai_search_model,
            "LLM model for AI Search chat"
        )

    db.commit()

    # Return updated config
    return get_ai_config(db, _admin)


# --- Legacy Search Strategy Endpoints (backward compatibility) ---
@router.get("/search-strategy", response_model=SearchStrategyResponse)
def get_search_strategy(
    db: DbSession,
    _admin: AdminUser,
) -> SearchStrategyResponse:
    """Get the current search strategy setting."""
    setting = db.query(AppSettings).filter(
        AppSettings.key == "search_strategy"
    ).first()

    if not setting:
        return SearchStrategyResponse(strategy=SearchStrategy.SERPER)

    try:
        strategy = SearchStrategy(setting.value)
    except ValueError:
        strategy = SearchStrategy.SERPER

    return SearchStrategyResponse(strategy=strategy)


@router.put("/search-strategy", response_model=SearchStrategyResponse)
def set_search_strategy(
    db: DbSession,
    _admin: AdminUser,
    request: SearchStrategyRequest,
) -> SearchStrategyResponse:
    """Update the search strategy setting."""
    setting = db.query(AppSettings).filter(
        AppSettings.key == "search_strategy"
    ).first()

    if setting:
        setting.value = request.strategy.value
    else:
        setting = AppSettings(
            key="search_strategy",
            value=request.strategy.value,
            description="Web search provider",
        )
        db.add(setting)

    # Also update new key
    _set_setting(
        db, "web_search.provider",
        request.strategy.value,
        "Web search provider"
    )

    db.commit()

    return SearchStrategyResponse(strategy=request.strategy)

