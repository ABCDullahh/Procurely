"""Provider seeder - seeds DataProvider table from DEFAULT_PROVIDERS."""

import logging

from sqlalchemy.orm import Session

from app.models.data_provider import DEFAULT_PROVIDERS, DataProvider

logger = logging.getLogger(__name__)


def seed_providers(db: Session) -> None:
    """
    Seed DataProvider table from DEFAULT_PROVIDERS constant.

    - If table is empty, seeds all providers
    - If table has entries, only adds missing providers (does not update existing)
    """
    existing_names = {p.name for p in db.query(DataProvider.name).all()}

    providers_to_add = []
    for provider_data in DEFAULT_PROVIDERS:
        if provider_data["name"] not in existing_names:
            provider = DataProvider(
                name=provider_data["name"],
                provider_type=provider_data["provider_type"],
                display_name=provider_data["display_name"],
                description=provider_data.get("description"),
                requires_api_key=provider_data.get("requires_api_key", False),
                api_key_provider=provider_data.get("api_key_provider"),
                is_enabled=provider_data.get("is_enabled", True),
                is_default=provider_data.get("is_default", False),
                is_free=provider_data.get("is_free", False),
            )
            providers_to_add.append(provider)
            db.add(provider)

    if providers_to_add:
        db.commit()
        logger.info(f"Seeded {len(providers_to_add)} new providers: {[p.name for p in providers_to_add]}")
    else:
        logger.debug("No new providers to seed")
