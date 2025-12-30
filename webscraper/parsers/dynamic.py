"""
Dynamic page parser using Playwright for JavaScript-rendered content.
"""

from typing import Optional
from urllib.parse import urljoin

from webscraper.core.config import PaginationConfig
from webscraper.utils.logging import get_logger

logger = get_logger(__name__)

# Lazy import for Playwright (optional dependency)
_playwright_available = None


def _check_playwright() -> bool:
    """Check if Playwright is available."""
    global _playwright_available
    if _playwright_available is None:
        try:
            import playwright
            _playwright_available = True
        except ImportError:
            _playwright_available = False
    return _playwright_available


class DynamicParser:
    """Parse JavaScript-rendered pages using Playwright."""
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        Initialize dynamic parser.
        
        Args:
            headless: Run browser in headless mode
            timeout: Page load timeout in milliseconds
        """
        if not _check_playwright():
            raise ImportError(
                "Playwright is required for dynamic page parsing. "
                "Install it with: pip install 'webscraper[playwright]' && playwright install chromium"
            )
        
        self.headless = headless
        self.timeout = timeout
        self._playwright = None
        self._browser = None
    
    async def start(self) -> None:
        """Start the browser."""
        from playwright.async_api import async_playwright
        
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        logger.info("Started Playwright browser")
    
    async def stop(self) -> None:
        """Stop the browser."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.info("Stopped Playwright browser")
    
    async def fetch_page(
        self,
        url: str,
        wait_for: Optional[str] = None,
    ) -> str:
        """
        Fetch a page and return rendered HTML.
        
        Args:
            url: URL to fetch
            wait_for: CSS selector to wait for before extracting content
            
        Returns:
            Rendered HTML content
        """
        if not self._browser:
            await self.start()
        
        page = await self._browser.new_page()
        try:
            await page.goto(url, timeout=self.timeout)
            
            if wait_for:
                await page.wait_for_selector(wait_for, timeout=self.timeout)
            else:
                # Wait for network to be idle
                await page.wait_for_load_state("networkidle")
            
            html = await page.content()
            return html
        finally:
            await page.close()
    
    def get_next_page_url(
        self,
        soup,
        current_url: str,
        pagination: PaginationConfig,
    ) -> Optional[str]:
        """Get the next page URL based on pagination configuration."""
        if pagination.strategy == "none" or not pagination.selector:
            return None
        
        if pagination.strategy == "next_button":
            next_link = soup.select_one(pagination.selector)
            if next_link and next_link.has_attr('href'):
                return urljoin(current_url, next_link['href'])
        
        return None
    
    async def __aenter__(self) -> "DynamicParser":
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.stop()
