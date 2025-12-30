"""
WebScraper - A professional, async-capable web scraper with CLI support.
"""

__version__ = "1.0.0"

from webscraper.core.scraper import Scraper
from webscraper.core.config import ScraperConfig

__all__ = ["Scraper", "ScraperConfig", "__version__"]
