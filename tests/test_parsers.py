"""
Tests for the parsers.
"""

import pytest
from bs4 import BeautifulSoup

from webscraper.parsers.static import StaticParser
from webscraper.core.config import PaginationConfig


class TestStaticParser:
    """Tests for StaticParser."""
    
    def test_parse_html(self, sample_html):
        """Test parsing HTML content."""
        parser = StaticParser()
        soup = parser.parse(sample_html)
        
        assert soup is not None
        assert soup.title.text == "Test Page"
    
    def test_get_next_page_url(self, sample_html):
        """Test getting next page URL."""
        parser = StaticParser()
        soup = parser.parse(sample_html)
        
        pagination = PaginationConfig(
            strategy="next_button",
            selector="li.next > a",
            max_pages=10
        )
        
        next_url = parser.get_next_page_url(soup, "http://test.com/page/1", pagination)
        
        assert next_url == "http://test.com/page/2"
    
    def test_no_next_page(self, sample_html_no_next):
        """Test handling pages without next button."""
        parser = StaticParser()
        soup = parser.parse(sample_html_no_next)
        
        pagination = PaginationConfig(
            strategy="next_button",
            selector="li.next > a",
            max_pages=10
        )
        
        next_url = parser.get_next_page_url(soup, "http://test.com/page/1", pagination)
        
        assert next_url is None
    
    def test_pagination_disabled(self, sample_html):
        """Test with pagination disabled."""
        parser = StaticParser()
        soup = parser.parse(sample_html)
        
        pagination = PaginationConfig(strategy="none", max_pages=10)
        
        next_url = parser.get_next_page_url(soup, "http://test.com/", pagination)
        
        assert next_url is None
