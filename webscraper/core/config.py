"""
Pydantic configuration models for the web scraper.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field, HttpUrl


class SessionConfig(BaseModel):
    """Session configuration for requests."""
    
    rotate_user_agent: bool = Field(default=True, description="Rotate User-Agent headers")
    proxies: list[str] = Field(default_factory=list, description="List of proxy URLs")
    timeout: float = Field(default=30.0, description="Request timeout in seconds")


class FieldSelector(BaseModel):
    """Configuration for a single field selector."""
    
    selector: str = Field(..., description="CSS selector for the field")
    attribute: Optional[str] = Field(default=None, description="Attribute to extract (e.g., 'href', 'title')")
    type: Literal["text", "html", "attribute"] = Field(default="text", description="Type of extraction")


class SelectorsConfig(BaseModel):
    """Selectors configuration for data extraction."""
    
    item_container: str = Field(..., description="CSS selector for item containers")
    fields: dict[str, FieldSelector | str] = Field(..., description="Field selectors")


class PaginationConfig(BaseModel):
    """Pagination configuration."""
    
    strategy: Literal["next_button", "page_number", "infinite_scroll", "none"] = Field(
        default="next_button", 
        description="Pagination strategy"
    )
    selector: Optional[str] = Field(default=None, description="Selector for next page element")
    max_pages: int = Field(default=10, description="Maximum pages to scrape")
    page_param: Optional[str] = Field(default=None, description="URL parameter for page number")


class OutputConfig(BaseModel):
    """Output configuration."""
    
    format: Literal["csv", "json", "parquet", "sqlite", "postgresql"] = Field(
        default="csv",
        description="Output format"
    )
    path: str = Field(default="./output/data", description="Output file path (without extension)")
    connection_string: Optional[str] = Field(default=None, description="Database connection string")
    table_name: Optional[str] = Field(default="scraped_data", description="Database table name")


class ResumeConfig(BaseModel):
    """Resume/checkpoint configuration."""
    
    enabled: bool = Field(default=True, description="Enable resume capability")
    checkpoint_dir: str = Field(default="./.scraper_state", description="Checkpoint directory")


class ScraperConfig(BaseModel):
    """Main scraper configuration."""
    
    base_url: str = Field(..., description="Base URL to scrape")
    concurrency: int = Field(default=5, ge=1, le=20, description="Concurrent requests limit")
    rate_limit: float = Field(default=1.0, ge=0.1, description="Delay between requests in seconds")
    max_retries: int = Field(default=3, ge=1, description="Maximum retry attempts")
    renderer: Literal["static", "dynamic"] = Field(
        default="static",
        description="Use 'dynamic' for JavaScript-rendered pages"
    )
    
    session: SessionConfig = Field(default_factory=SessionConfig)
    selectors: SelectorsConfig
    pagination: PaginationConfig = Field(default_factory=PaginationConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    resume: ResumeConfig = Field(default_factory=ResumeConfig)
    
    @classmethod
    def from_yaml(cls, path: str) -> "ScraperConfig":
        """Load configuration from a YAML file."""
        import yaml
        
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Handle legacy config format
        if 'scraper' in data:
            # New format with nested 'scraper' key
            return cls(**data['scraper'])
        
        # Legacy format - transform to new structure
        return cls._from_legacy(data)
    
    @classmethod
    def _from_legacy(cls, data: dict) -> "ScraperConfig":
        """Transform legacy config format to new format."""
        # Transform selectors
        fields = {}
        if 'selectors' in data and 'fields' in data['selectors']:
            for name, selector_str in data['selectors']['fields'].items():
                if "::attr(" in selector_str:
                    selector, attr_part = selector_str.split("::attr(")
                    attr_name = attr_part.rstrip(")")
                    fields[name] = FieldSelector(
                        selector=selector.strip(),
                        attribute=attr_name,
                        type="attribute"
                    )
                elif "::text" in selector_str:
                    selector = selector_str.replace("::text", "").strip()
                    fields[name] = FieldSelector(selector=selector, type="text")
                else:
                    fields[name] = FieldSelector(selector=selector_str, type="text")
        
        selectors = SelectorsConfig(
            item_container=data.get('selectors', {}).get('item_container', ''),
            fields=fields
        )
        
        # Transform pagination
        pagination_data = data.get('pagination', {})
        pagination = PaginationConfig(
            strategy=pagination_data.get('strategy', 'next_button'),
            selector=pagination_data.get('next_button_selector'),
            max_pages=pagination_data.get('max_pages', 10)
        )
        
        # Build config
        return cls(
            base_url=data.get('base_url', ''),
            rate_limit=data.get('rate_limit_delay', 1.0),
            max_retries=data.get('max_retries', 3),
            selectors=selectors,
            pagination=pagination,
            output=OutputConfig(
                format=data.get('output_format', 'csv'),
                path=data.get('output_file', './output/data')
            )
        )
    
    def to_yaml(self, path: str) -> None:
        """Save configuration to a YAML file."""
        import yaml
        
        with open(path, 'w') as f:
            yaml.dump({'scraper': self.model_dump()}, f, default_flow_style=False, sort_keys=False)
