"""
CSS selector-based extractor.
"""

from typing import Any

from bs4 import BeautifulSoup

from webscraper.extractors.base import BaseExtractor
from webscraper.core.config import SelectorsConfig, FieldSelector
from webscraper.utils.logging import get_logger

logger = get_logger(__name__)


class CSSExtractor(BaseExtractor):
    """Extract data using CSS selectors."""
    
    def extract(self, soup: BeautifulSoup, selectors: SelectorsConfig) -> list[dict[str, Any]]:
        """
        Extract all items from a page using CSS selectors.
        
        Args:
            soup: BeautifulSoup object of the page
            selectors: Selector configuration
            
        Returns:
            List of extracted items
        """
        items = []
        containers = soup.select(selectors.item_container)
        
        for container in containers:
            item = {}
            for field_name, field_config in selectors.fields.items():
                # Handle string shorthand (legacy format)
                if isinstance(field_config, str):
                    field_config = self._parse_legacy_selector(field_config)
                
                item[field_name] = self.extract_field(container, field_config)
            
            items.append(item)
        
        return items
    
    def extract_field(self, container: BeautifulSoup, field_config: FieldSelector) -> Any:
        """
        Extract a single field from a container.
        
        Args:
            container: BeautifulSoup element
            field_config: Field configuration
            
        Returns:
            Extracted value or None
        """
        element = container.select_one(field_config.selector)
        
        if element is None:
            return None
        
        if field_config.type == "attribute" and field_config.attribute:
            return element.get(field_config.attribute)
        elif field_config.type == "html":
            return str(element)
        else:  # text
            return element.get_text(strip=True)
    
    def _parse_legacy_selector(self, selector_str: str) -> FieldSelector:
        """Parse legacy selector format (e.g., 'h3 > a::attr(title)')."""
        if "::attr(" in selector_str:
            selector, attr_part = selector_str.split("::attr(")
            attr_name = attr_part.rstrip(")")
            return FieldSelector(
                selector=selector.strip(),
                attribute=attr_name,
                type="attribute"
            )
        elif "::text" in selector_str:
            selector = selector_str.replace("::text", "").strip()
            return FieldSelector(selector=selector, type="text")
        else:
            return FieldSelector(selector=selector_str, type="text")
