"""Service for fetching available models from LLM providers."""

import logging
import time
from datetime import datetime, timezone

import httpx

from app.schemas.api_key import ProviderModel

logger = logging.getLogger(__name__)

# In-memory cache with TTL (seconds)
_MODEL_CACHE: dict[str, tuple[list[ProviderModel], float]] = {}
CACHE_TTL_SECONDS = 600  # 10 minutes


def _is_cache_valid(provider: str) -> bool:
    """Check if cached models are still valid."""
    if provider not in _MODEL_CACHE:
        return False
    _, cached_at = _MODEL_CACHE[provider]
    return (time.time() - cached_at) < CACHE_TTL_SECONDS


def _get_cached_models(provider: str) -> list[ProviderModel] | None:
    """Get cached models if valid."""
    if _is_cache_valid(provider):
        models, _ = _MODEL_CACHE[provider]
        return models
    return None


def _cache_models(provider: str, models: list[ProviderModel]) -> None:
    """Cache models with current timestamp."""
    _MODEL_CACHE[provider] = (models, time.time())


async def fetch_gemini_models_live(api_key: str) -> list[ProviderModel] | None:
    """Fetch models from Gemini ListModels API.
    
    Returns None if fetch fails (for fallback to curated list).
    """
    # Check cache first
    cached = _get_cached_models("GEMINI")
    if cached is not None:
        logger.debug("Using cached Gemini models")
        return cached

    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)

            if response.status_code == 401 or response.status_code == 403:
                logger.warning("Gemini API key invalid for ListModels")
                return None

            if response.status_code != 200:
                logger.warning(f"Gemini ListModels failed: {response.status_code}")
                return None

            data = response.json()
            models_data = data.get("models", [])

            models: list[ProviderModel] = []
            for m in models_data:
                name = m.get("name", "")
                # Filter to only models supporting generateContent
                supported_methods = m.get("supportedGenerationMethods", [])
                if "generateContent" not in supported_methods:
                    continue

                # Extract model id from full name (e.g., "models/gemini-1.5-flash" -> "gemini-1.5-flash")
                model_id = name.replace("models/", "")

                # Create human-friendly label
                display_name = m.get("displayName", model_id)

                # Determine supports
                supports = ["text"]
                # Gemini supports JSON extraction through prompting
                supports.append("json")

                models.append(ProviderModel(
                    id=model_id,
                    label=display_name,
                    supports=supports,
                ))

            # Sort to put recommended models first
            priority_order = ["gemini-2", "gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"]
            def sort_key(model: ProviderModel) -> int:
                for i, prefix in enumerate(priority_order):
                    if model.id.startswith(prefix):
                        return i
                return 100

            models.sort(key=sort_key)

            # Cache results
            _cache_models("GEMINI", models)
            logger.info(f"Fetched {len(models)} Gemini models live")
            return models

    except httpx.TimeoutException:
        logger.warning("Gemini ListModels timed out")
        return None
    except Exception as e:
        logger.warning(f"Gemini ListModels failed: {e}")
        return None


async def fetch_openai_models_live(api_key: str) -> list[ProviderModel] | None:
    """Fetch models from OpenAI GET /v1/models.
    
    Returns None if fetch fails (for fallback to curated list).
    """
    # Check cache first
    cached = _get_cached_models("OPENAI")
    if cached is not None:
        logger.debug("Using cached OpenAI models")
        return cached

    url = "https://api.openai.com/v1/models"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {api_key}"}
            )

            if response.status_code == 401:
                logger.warning("OpenAI API key invalid for list models")
                return None

            if response.status_code != 200:
                logger.warning(f"OpenAI list models failed: {response.status_code}")
                return None

            data = response.json()
            models_data = data.get("data", [])

            models: list[ProviderModel] = []
            for m in models_data:
                model_id = m.get("id", "")

                # Filter to GPT models only
                if not model_id.startswith("gpt-"):
                    continue

                # Skip older/deprecated variants
                if any(skip in model_id for skip in ["-instruct", "-0301", "-0314", "-0613", "-1106", "-0125"]):
                    continue

                # Create label
                label = model_id.replace("-", " ").title()
                if "4o" in model_id:
                    label = f"GPT-4o {'Mini' if 'mini' in model_id else ''}"
                elif "4-turbo" in model_id:
                    label = "GPT-4 Turbo"
                elif "4" in model_id:
                    label = "GPT-4"
                elif "3.5" in model_id:
                    label = "GPT-3.5 Turbo"

                models.append(ProviderModel(
                    id=model_id,
                    label=label.strip(),
                    supports=["text", "json"],
                ))

            # Sort by preference
            priority = {"gpt-4o": 0, "gpt-4o-mini": 1, "gpt-4-turbo": 2, "gpt-4": 3, "gpt-3.5-turbo": 4}
            models.sort(key=lambda m: priority.get(m.id, 10))

            # Cache results
            _cache_models("OPENAI", models)
            logger.info(f"Fetched {len(models)} OpenAI models live")
            return models

    except httpx.TimeoutException:
        logger.warning("OpenAI list models timed out")
        return None
    except Exception as e:
        logger.warning(f"OpenAI list models failed: {e}")
        return None


def get_cache_timestamp(provider: str) -> datetime | None:
    """Get the timestamp when models were cached."""
    if provider in _MODEL_CACHE:
        _, cached_at = _MODEL_CACHE[provider]
        return datetime.fromtimestamp(cached_at, tz=timezone.utc)
    return None
