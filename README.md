# WebScraper

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/yourusername/webscraper/workflows/Tests/badge.svg)](https://github.com/yourusername/webscraper/actions)

A professional, async-capable web scraper with CLI support, Playwright integration for JavaScript-rendered pages, and multiple export formats.

## Features

- **Async Scraping** - Concurrent page fetching with configurable concurrency
- **JS Rendering** - Playwright integration for JavaScript-heavy sites
- **Multiple Formats** - Export to CSV, JSON, Parquet, SQLite, or PostgreSQL
- **Smart Retry** - Exponential backoff with configurable retries
- **Resume Support** - Checkpoint and resume interrupted scrapes
- **Proxy Rotation** - Built-in proxy and User-Agent rotation
- **Type Safe** - Full Pydantic validation for configurations
- **CLI Interface** - Easy-to-use command-line interface

## Installation

```bash
# Basic installation
pip install -e .

# With Playwright for JavaScript rendering
pip install -e ".[playwright]"
playwright install chromium

# With database export support
pip install -e ".[database]"

# Full installation with dev tools
pip install -e ".[all]"
```

## Quick Start

### 1. Generate a config file

```bash
webscraper init config.yaml --url "http://books.toscrape.com/"
```

### 2. Edit the config to match your target site

```yaml
scraper:
  base_url: "http://books.toscrape.com/"
  concurrency: 5
  renderer: "static"

  selectors:
    item_container: "article.product_pod"
    fields:
      title:
        selector: "h3 > a"
        attribute: "title"
      price:
        selector: ".price_color"
        type: "text"

  pagination:
    strategy: "next_button"
    selector: "li.next > a"
    max_pages: 5

  output:
    format: "csv"
    path: "./output/books"
```

### 3. Run the scraper

```bash
webscraper run config.yaml
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `webscraper run config.yaml` | Run scraper with config |
| `webscraper init output.yaml` | Generate sample config |
| `webscraper validate config.yaml` | Validate config file |
| `webscraper resume <job_id>` | Resume interrupted scrape |
| `webscraper jobs` | List saved job states |

### CLI Options

```bash
# Override output format
webscraper run config.yaml --format json

# Limit pages
webscraper run config.yaml --max-pages 3

# Adjust concurrency
webscraper run config.yaml --concurrency 10

# Verbose output
webscraper -v run config.yaml
```

## Configuration Reference

### Scraper Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `base_url` | string | required | Starting URL |
| `concurrency` | int | 5 | Max concurrent requests (1-20) |
| `rate_limit` | float | 1.0 | Delay between requests (seconds) |
| `max_retries` | int | 3 | Retry attempts per request |
| `renderer` | string | "static" | "static" or "dynamic" |

### Session Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `rotate_user_agent` | bool | true | Rotate User-Agent headers |
| `proxies` | list | [] | List of proxy URLs |
| `timeout` | float | 30.0 | Request timeout (seconds) |

### Output Formats

- **csv** - CSV file
- **json** - JSON array
- **parquet** - Apache Parquet
- **sqlite** - SQLite database
- **postgresql** - PostgreSQL database

## Python API

```python
import asyncio
from webscraper import Scraper, ScraperConfig

# From config file
scraper = Scraper.from_yaml("config.yaml")

# Or programmatically
config = ScraperConfig(
    base_url="http://books.toscrape.com/",
    selectors=...,
)
scraper = Scraper(config)

# Run
data = asyncio.run(scraper.run())
print(f"Scraped {len(data)} items")
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=webscraper --cov-report=html
```

## License

MIT License - see [LICENSE](LICENSE) for details.
