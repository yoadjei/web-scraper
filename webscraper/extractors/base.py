"""
Base extractor class.
"""

from abc import ABC, abstractmethod
from typing import Any

from bs4 import BeautifulSoup


class BaseExtractor(ABC):
    """Abstract base class for data extractors."""
    
    @abstractmethod
    def extract(self, soup: BeautifulSoup, config: dict) -> list[dict[str, Any]]:
        """
        Extract data from parsed HTML.
        
        Args:
            soup: BeautifulSoup object of the page
            config: Selector configuration
            
        Returns:
            List of extracted items as dictionaries
        """
        pass
    
    @abstractmethod
    def extract_field(self, container: BeautifulSoup, field_config: dict) -> Any:
        """
        Extract a single field from a container element.
        
        Args:
            container: BeautifulSoup element containing the data
            field_config: Configuration for this field
            
        Returns:
            Extracted value
        """
        pass
