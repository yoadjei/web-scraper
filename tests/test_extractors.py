"""
Tests for the CSS extractor.
"""

import pytest
from bs4 import BeautifulSoup

from webscraper.extractors.css import CSSExtractor
from webscraper.core.config import SelectorsConfig, FieldSelector


class TestCSSExtractor:
    """Tests for CSSExtractor."""
    
    def test_extract_items(self, sample_html):
        """Test extracting multiple items from HTML."""
        extractor = CSSExtractor()
        soup = BeautifulSoup(sample_html, 'html.parser')
        
        selectors = SelectorsConfig(
            item_container="article.product_pod",
            fields={
                "title": FieldSelector(selector="h3 > a", attribute="title", type="attribute"),
                "price": FieldSelector(selector=".price_color", type="text"),
            }
        )
        
        items = extractor.extract(soup, selectors)
        
        assert len(items) == 3
        assert items[0]["title"] == "Product One"
        assert items[0]["price"] == "£10.00"
        assert items[1]["title"] == "Product Two"
        assert items[2]["title"] == "Product Three"
    
    def test_extract_text_field(self, sample_html):
        """Test extracting text content."""
        extractor = CSSExtractor()
        soup = BeautifulSoup(sample_html, 'html.parser')
        container = soup.select_one("article.product_pod")
        
        field_config = FieldSelector(selector=".price_color", type="text")
        value = extractor.extract_field(container, field_config)
        
        assert value == "£10.00"
    
    def test_extract_attribute_field(self, sample_html):
        """Test extracting attribute value."""
        extractor = CSSExtractor()
        soup = BeautifulSoup(sample_html, 'html.parser')
        container = soup.select_one("article.product_pod")
        
        field_config = FieldSelector(selector="h3 > a", attribute="title", type="attribute")
        value = extractor.extract_field(container, field_config)
        
        assert value == "Product One"
    
    def test_extract_missing_element(self, sample_html):
        """Test handling missing elements."""
        extractor = CSSExtractor()
        soup = BeautifulSoup(sample_html, 'html.parser')
        container = soup.select_one("article.product_pod")
        
        field_config = FieldSelector(selector=".nonexistent", type="text")
        value = extractor.extract_field(container, field_config)
        
        assert value is None
    
    def test_legacy_selector_format(self, sample_html):
        """Test parsing legacy selector format."""
        extractor = CSSExtractor()
        
        # Test ::attr() format
        field = extractor._parse_legacy_selector("h3 > a::attr(title)")
        assert field.selector == "h3 > a"
        assert field.attribute == "title"
        assert field.type == "attribute"
        
        # Test ::text format
        field = extractor._parse_legacy_selector(".price_color::text")
        assert field.selector == ".price_color"
        assert field.type == "text"
        
        # Test plain selector
        field = extractor._parse_legacy_selector(".price_color")
        assert field.selector == ".price_color"
        assert field.type == "text"
