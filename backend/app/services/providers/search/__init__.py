"""Search providers package - web search implementations."""

# Import providers to trigger registration
from app.services.providers.search.serpapi_shopping import SerpAPIShoppingProvider
from app.services.providers.search.serper import SerperSearchProvider
from app.services.providers.search.tavily import TavilySearchProvider

__all__ = [
    "SerperSearchProvider",
    "SerpAPIShoppingProvider",
    "TavilySearchProvider",
]
