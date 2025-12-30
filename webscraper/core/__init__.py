"""WebScraper core module."""

from webscraper.core.scraper import Scraper
from webscraper.core.config import ScraperConfig
from webscraper.core.session import SessionManager

__all__ = ["Scraper", "ScraperConfig", "SessionManager"]
