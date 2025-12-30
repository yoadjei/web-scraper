"""
Pytest configuration and fixtures.
"""

import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil

# Sample HTML for testing
SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head><title>Test Page</title></head>
<body>
    <div class="products">
        <article class="product_pod">
            <h3><a href="/product/1" title="Product One">Product One</a></h3>
            <p class="price_color">£10.00</p>
        </article>
        <article class="product_pod">
            <h3><a href="/product/2" title="Product Two">Product Two</a></h3>
            <p class="price_color">£20.00</p>
        </article>
        <article class="product_pod">
            <h3><a href="/product/3" title="Product Three">Product Three</a></h3>
            <p class="price_color">£30.00</p>
        </article>
    </div>
    <nav>
        <li class="next"><a href="/page/2">Next</a></li>
    </nav>
</body>
</html>
"""

SAMPLE_HTML_NO_NEXT = """
<!DOCTYPE html>
<html>
<head><title>Last Page</title></head>
<body>
    <div class="products">
        <article class="product_pod">
            <h3><a href="/product/4" title="Product Four">Product Four</a></h3>
            <p class="price_color">£40.00</p>
        </article>
    </div>
</body>
</html>
"""

SAMPLE_CONFIG = """
base_url: "http://test.example.com/"
rate_limit_delay: 0.1
max_retries: 2
output_format: "csv"
output_file: "test_output"
pagination:
  strategy: "next_button"
  next_button_selector: "li.next > a"
  max_pages: 3
selectors:
  item_container: "article.product_pod"
  fields:
    title: "h3 > a::attr(title)"
    price: ".price_color::text"
"""


@pytest.fixture
def sample_html():
    """Sample HTML for testing."""
    return SAMPLE_HTML


@pytest.fixture
def sample_html_no_next():
    """Sample HTML without next page."""
    return SAMPLE_HTML_NO_NEXT


@pytest.fixture
def sample_config():
    """Sample configuration content."""
    return SAMPLE_CONFIG


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test output."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def config_file(temp_dir, sample_config):
    """Create a temporary config file."""
    config_path = temp_dir / "config.yaml"
    config_path.write_text(sample_config)
    return config_path


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
