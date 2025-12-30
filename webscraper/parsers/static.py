"""
Static HTML parser using BeautifulSoup.
"""

from bs4 import BeautifulSoup
from typing import Optional
from urllib.parse import urljoin

from webscraper.core.config import PaginationConfig
from webscraper.utils.logging import get_logger

logger = get_logger(__name__)


class StaticParser:
    """Parse static HTML content with BeautifulSoup."""
    
    def __init__(self, parser: str = "html.parser"):
        self.parser = parser
    
    def parse(self, html: str) -> BeautifulSoup:
        """
        Parse HTML content.
        
        Args:
            html: Raw HTML string
            
        Returns:
            BeautifulSoup object
        """
        return BeautifulSoup(html, self.parser)
    
    def get_next_page_url(
        self,
        soup: BeautifulSoup,
        current_url: str,
        pagination: PaginationConfig,
    ) -> Optional[str]:
        """
        Get the next page URL based on pagination configuration.
        
        Args:
            soup: BeautifulSoup object of the current page
            current_url: Current page URL
            pagination: Pagination configuration
            
        Returns:
            Next page URL or None if no more pages
        """
        if pagination.strategy == "none" or not pagination.selector:
            return None
        
        if pagination.strategy == "next_button":
            return self._get_next_button_url(soup, current_url, pagination.selector)
        
        # Add more strategies as needed
        return None
    
    def _get_next_button_url(
        self,
        soup: BeautifulSoup,
        current_url: str,
        selector: str,
    ) -> Optional[str]:
        """Get URL from next button."""
        next_link = soup.select_one(selector)
        
        if next_link and next_link.has_attr('href'):
            return urljoin(current_url, next_link['href'])
        
        return None
