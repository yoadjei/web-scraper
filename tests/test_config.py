"""
Tests for configuration loading.
"""

import pytest
from pathlib import Path

from webscraper.core.config import ScraperConfig, SelectorsConfig, FieldSelector


class TestScraperConfig:
    """Tests for ScraperConfig."""
    
    def test_load_legacy_config(self, config_file):
        """Test loading legacy config format."""
        config = ScraperConfig.from_yaml(str(config_file))
        
        assert config.base_url == "http://test.example.com/"
        assert config.rate_limit == 0.1
        assert config.max_retries == 2
        assert config.pagination.max_pages == 3
        assert config.pagination.strategy == "next_button"
    
    def test_selectors_transform(self, config_file):
        """Test that legacy selectors are properly transformed."""
        config = ScraperConfig.from_yaml(str(config_file))
        
        assert "title" in config.selectors.fields
        assert "price" in config.selectors.fields
        
        title_field = config.selectors.fields["title"]
        assert isinstance(title_field, FieldSelector)
        assert title_field.attribute == "title"
    
    def test_field_selector_model(self):
        """Test FieldSelector model."""
        field = FieldSelector(selector=".test", type="text")
        assert field.selector == ".test"
        assert field.type == "text"
        assert field.attribute is None
        
        field_attr = FieldSelector(selector="a", attribute="href", type="attribute")
        assert field_attr.attribute == "href"
    
    def test_config_defaults(self):
        """Test configuration defaults."""
        config = ScraperConfig(
            base_url="http://example.com",
            selectors=SelectorsConfig(
                item_container=".item",
                fields={"name": FieldSelector(selector=".name", type="text")}
            )
        )
        
        assert config.concurrency == 5
        assert config.rate_limit == 1.0
        assert config.max_retries == 3
        assert config.renderer == "static"
        assert config.session.rotate_user_agent is True
        assert config.resume.enabled is True
    
    def test_config_validation(self):
        """Test configuration validation."""
        with pytest.raises(ValueError):
            ScraperConfig(
                base_url="http://example.com",
                concurrency=100,  # Too high, max is 20
                selectors=SelectorsConfig(
                    item_container=".item",
                    fields={"name": FieldSelector(selector=".name", type="text")}
                )
            )
