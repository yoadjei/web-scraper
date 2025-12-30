"""
Command-line interface for WebScraper.
"""

import asyncio
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from webscraper import __version__
from webscraper.core.config import ScraperConfig
from webscraper.core.scraper import Scraper
from webscraper.utils.logging import setup_logging, print_success, print_error, print_info
from webscraper.utils.state import StateManager

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="webscraper")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def main(verbose: bool):
    """WebScraper - A professional async web scraper."""
    setup_logging(level="DEBUG" if verbose else "INFO", verbose=verbose)


@main.command()
@click.argument("config_path", type=click.Path(exists=True))
@click.option("--output", "-o", help="Override output path")
@click.option("--format", "-f", type=click.Choice(["csv", "json", "parquet", "sqlite"]), help="Override output format")
@click.option("--max-pages", "-p", type=int, help="Override max pages to scrape")
@click.option("--concurrency", "-c", type=int, help="Override concurrency limit")
def run(config_path: str, output: Optional[str], format: Optional[str], max_pages: Optional[int], concurrency: Optional[int]):
    """Run the web scraper with the given configuration file."""
    try:
        config = ScraperConfig.from_yaml(config_path)
        
        # Apply CLI overrides
        if output:
            config.output.path = output
        if format:
            config.output.format = format
        if max_pages:
            config.pagination.max_pages = max_pages
        if concurrency:
            config.concurrency = concurrency
        
        scraper = Scraper(config)
        asyncio.run(scraper.run())
        
    except FileNotFoundError:
        print_error(f"Config file not found: {config_path}")
        raise SystemExit(1)
    except Exception as e:
        print_error(f"Scraping failed: {e}")
        raise SystemExit(1)


@main.command()
@click.argument("output_path", type=click.Path(), default="config.yaml")
@click.option("--url", "-u", default="http://books.toscrape.com/", help="Base URL to scrape")
def init(output_path: str, url: str):
    """Generate a sample configuration file."""
    sample_config = f"""# WebScraper Configuration
# Generated for: {url}

scraper:
  base_url: "{url}"
  concurrency: 5
  rate_limit: 1.0
  max_retries: 3
  renderer: "static"  # Use "dynamic" for JavaScript-rendered pages

  session:
    rotate_user_agent: true
    proxies: []  # Add proxy URLs here for rotation

  selectors:
    item_container: "article.product_pod"  # CSS selector for item containers
    fields:
      title:
        selector: "h3 > a"
        attribute: "title"
        type: "attribute"
      price:
        selector: ".price_color"
        type: "text"

  pagination:
    strategy: "next_button"  # Options: next_button, page_number, none
    selector: "li.next > a"
    max_pages: 5

  output:
    format: "csv"  # Options: csv, json, parquet, sqlite, postgresql
    path: "./output/scraped_data"
    # For database exports:
    # connection_string: "postgresql://user:pass@localhost:5432/db"
    # table_name: "scraped_data"

  resume:
    enabled: true
    checkpoint_dir: "./.scraper_state"
"""
    
    output = Path(output_path)
    output.write_text(sample_config)
    print_success(f"Created sample config: {output_path}")
    print_info("Edit the config file to match your target website's structure")


@main.command()
@click.argument("config_path", type=click.Path(exists=True))
def validate(config_path: str):
    """Validate a configuration file."""
    try:
        config = ScraperConfig.from_yaml(config_path)
        print_success(f"Configuration is valid!")
        
        # Show summary
        console.print("\n[bold]Configuration Summary:[/]")
        console.print(f"  Base URL: {config.base_url}")
        console.print(f"  Renderer: {config.renderer}")
        console.print(f"  Concurrency: {config.concurrency}")
        console.print(f"  Max Pages: {config.pagination.max_pages}")
        console.print(f"  Output Format: {config.output.format}")
        console.print(f"  Fields: {', '.join(config.selectors.fields.keys())}")
        
    except Exception as e:
        print_error(f"Invalid configuration: {e}")
        raise SystemExit(1)


@main.command()
@click.argument("job_id")
@click.option("--checkpoint-dir", "-d", default="./.scraper_state", help="Checkpoint directory")
def resume(job_id: str, checkpoint_dir: str):
    """Resume an interrupted scraping job."""
    state_manager = StateManager(checkpoint_dir)
    state = state_manager.load_state(job_id)
    
    if not state:
        print_error(f"Job not found: {job_id}")
        raise SystemExit(1)
    
    if state.completed:
        print_error(f"Job {job_id} is already completed")
        raise SystemExit(1)
    
    print_info(f"Resuming job {job_id}...")
    print_info(f"Progress: {state.pages_scraped} pages, {state.items_collected} items")
    
    # Load config and resume
    try:
        config = ScraperConfig.from_yaml("config.yaml")  # Default config path
        scraper = Scraper(config)
        asyncio.run(scraper.run(resume_job_id=job_id))
    except Exception as e:
        print_error(f"Resume failed: {e}")
        raise SystemExit(1)


@main.command()
@click.option("--checkpoint-dir", "-d", default="./.scraper_state", help="Checkpoint directory")
def jobs(checkpoint_dir: str):
    """List all saved scraping jobs."""
    state_manager = StateManager(checkpoint_dir)
    all_jobs = state_manager.list_jobs()
    
    if not all_jobs:
        print_info("No saved jobs found")
        return
    
    table = Table(title="Saved Jobs")
    table.add_column("Job ID", style="cyan")
    table.add_column("URL", style="blue")
    table.add_column("Pages", justify="right")
    table.add_column("Items", justify="right")
    table.add_column("Status", style="green")
    table.add_column("Last Updated")
    
    for job in all_jobs:
        status = "Completed" if job.completed else "In Progress"
        table.add_row(
            job.job_id,
            job.base_url[:40] + "..." if len(job.base_url) > 40 else job.base_url,
            str(job.pages_scraped),
            str(job.items_collected),
            status,
            job.last_updated[:19],
        )
    
    console.print(table)


if __name__ == "__main__":
    main()
