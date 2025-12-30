"""
Async web scraper engine.
"""

import asyncio
import hashlib
from typing import Optional, Any
from urllib.parse import urljoin

import aiohttp

from webscraper.core.config import ScraperConfig
from webscraper.core.session import SessionManager
from webscraper.extractors.css import CSSExtractor
from webscraper.parsers.static import StaticParser
from webscraper.exporters.file import FileExporter
from webscraper.exporters.database import DatabaseExporter
from webscraper.utils.logging import get_logger, create_progress, print_info, print_success, print_error
from webscraper.utils.retry import async_retry
from webscraper.utils.state import StateManager, ScrapeState

logger = get_logger(__name__)


class Scraper:
    """
    Async web scraper with support for concurrent requests,
    multiple parsers, and various export formats.
    """
    
    def __init__(self, config: ScraperConfig):
        """
        Initialize the scraper.
        
        Args:
            config: Scraper configuration
        """
        self.config = config
        self.session_manager = SessionManager(
            rotate_user_agent=config.session.rotate_user_agent,
            proxies=config.session.proxies,
            timeout=config.session.timeout,
        )
        self.extractor = CSSExtractor()
        self.parser = StaticParser()
        self.dynamic_parser = None
        self.state_manager = StateManager(config.resume.checkpoint_dir) if config.resume.enabled else None
        self._semaphore: Optional[asyncio.Semaphore] = None
    
    @classmethod
    def from_yaml(cls, config_path: str) -> "Scraper":
        """Create a scraper from a YAML config file."""
        config = ScraperConfig.from_yaml(config_path)
        return cls(config)
    
    def _generate_job_id(self) -> str:
        """Generate a unique job ID based on config."""
        config_str = f"{self.config.base_url}:{self.config.selectors.item_container}"
        return hashlib.md5(config_str.encode()).hexdigest()[:12]
    
    async def _init_dynamic_parser(self) -> None:
        """Initialize dynamic parser if needed."""
        if self.config.renderer == "dynamic" and self.dynamic_parser is None:
            from webscraper.parsers.dynamic import DynamicParser
            self.dynamic_parser = DynamicParser()
            await self.dynamic_parser.start()
    
    async def _cleanup_dynamic_parser(self) -> None:
        """Clean up dynamic parser."""
        if self.dynamic_parser:
            await self.dynamic_parser.stop()
            self.dynamic_parser = None
    
    @async_retry(max_attempts=3, delay=1.0, exceptions=(aiohttp.ClientError, asyncio.TimeoutError))
    async def _fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a page with retry logic.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content or None
        """
        async with self._semaphore:
            # Rate limiting
            await asyncio.sleep(self.config.rate_limit)
            
            if self.config.renderer == "dynamic":
                return await self.dynamic_parser.fetch_page(url)
            
            session = await self.session_manager.get_session()
            headers = self.session_manager.get_headers()
            proxy = self.session_manager.get_proxy()
            
            async with session.get(url, headers=headers, proxy=proxy) as response:
                response.raise_for_status()
                return await response.text()
    
    async def _scrape_page(self, url: str) -> tuple[list[dict[str, Any]], Optional[str]]:
        """
        Scrape a single page.
        
        Args:
            url: URL to scrape
            
        Returns:
            Tuple of (extracted items, next page URL)
        """
        html = await self._fetch_page(url)
        
        if not html:
            return [], None
        
        soup = self.parser.parse(html)
        items = self.extractor.extract(soup, self.config.selectors)
        
        # Get next page URL
        if self.config.renderer == "dynamic" and self.dynamic_parser:
            next_url = self.dynamic_parser.get_next_page_url(soup, url, self.config.pagination)
        else:
            next_url = self.parser.get_next_page_url(soup, url, self.config.pagination)
        
        return items, next_url
    
    def _get_exporter(self):
        """Get the appropriate exporter based on config."""
        output = self.config.output
        
        if output.format in ("csv", "json", "parquet"):
            return FileExporter(format=output.format)
        elif output.format == "sqlite":
            from webscraper.exporters.database import SQLiteExporter
            return SQLiteExporter(
                db_path=f"{output.path}.db",
                table_name=output.table_name or "scraped_data"
            )
        elif output.format == "postgresql":
            if not output.connection_string:
                raise ValueError("PostgreSQL requires a connection_string in config")
            return DatabaseExporter(
                connection_string=output.connection_string,
                table_name=output.table_name or "scraped_data"
            )
        else:
            raise ValueError(f"Unsupported output format: {output.format}")
    
    async def run(self, resume_job_id: Optional[str] = None) -> list[dict[str, Any]]:
        """
        Run the scraper.
        
        Args:
            resume_job_id: Optional job ID to resume
            
        Returns:
            List of all scraped items
        """
        self._semaphore = asyncio.Semaphore(self.config.concurrency)
        all_data: list[dict[str, Any]] = []
        state: Optional[ScrapeState] = None
        
        try:
            # Initialize dynamic parser if needed
            await self._init_dynamic_parser()
            
            # Handle resume
            if resume_job_id and self.state_manager:
                state = self.state_manager.load_state(resume_job_id)
                if state and not state.completed:
                    print_info(f"Resuming job {resume_job_id} from page {state.pages_scraped + 1}")
                    current_url = self.state_manager.get_resumable_url(state)
                    pages_scraped = state.pages_scraped
                else:
                    print_error(f"Cannot resume job {resume_job_id}")
                    state = None
            
            # Create new job if not resuming
            if not state:
                job_id = self._generate_job_id()
                if self.state_manager:
                    state = self.state_manager.create_job(job_id, self.config.base_url)
                current_url = self.config.base_url
                pages_scraped = 0
            
            max_pages = self.config.pagination.max_pages
            
            print_info(f"Starting scrape: {self.config.base_url}")
            print_info(f"Max pages: {max_pages}, Concurrency: {self.config.concurrency}")
            
            with create_progress() as progress:
                task = progress.add_task("Scraping pages...", total=max_pages)
                
                while current_url and pages_scraped < max_pages:
                    # Skip already scraped URLs
                    if state and current_url in state.urls_scraped:
                        pages_scraped += 1
                        progress.update(task, advance=1)
                        continue
                    
                    items, next_url = await self._scrape_page(current_url)
                    all_data.extend(items)
                    
                    # Update state
                    if state and self.state_manager:
                        self.state_manager.update_progress(state, current_url, len(items))
                    
                    logger.debug(f"Page {pages_scraped + 1}: {len(items)} items from {current_url}")
                    
                    current_url = next_url
                    pages_scraped += 1
                    progress.update(task, advance=1)
            
            # Mark job as completed
            if state and self.state_manager:
                self.state_manager.mark_completed(state)
            
            # Export data
            if all_data:
                exporter = self._get_exporter()
                await exporter.export(all_data, self.config.output.path)
            
            print_success(f"Scraping complete: {len(all_data)} items from {pages_scraped} pages")
            
            return all_data
            
        finally:
            await self._cleanup_dynamic_parser()
            await self.session_manager.close()
    
    async def __aenter__(self) -> "Scraper":
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self._cleanup_dynamic_parser()
        await self.session_manager.close()
