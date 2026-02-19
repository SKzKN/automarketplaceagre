import asyncio
import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class AsyncBaseScraper(ABC):
    """
    Abstract base class for all async car listing scrapers.

    Defines the interface for scraping operations without implementing
    HTTP client specifics. Subclasses must implement:
    - _get_session(): Create/get HTTP session
    - close(): Close HTTP session
    - fetch_page(): Fetch a URL and return HTML
    - get_listing_urls(): Get listing URLs from search pages
    - parse_listing(): Parse HTML into listing data

    Supports concurrent scraping with configurable batch sizes and rate limiting.
    """

    def __init__(
        self,
        base_url: str,
        site_name: str,
        batch_size: int = 10,
        request_delay: float = 0.5,
        request_timeout: int = 30,
    ):
        """
        Initialize async scraper.

        Args:
            base_url: Base URL of the website
            site_name: Name of the website for logging
            batch_size: Number of requests to process concurrently in one batch
            request_delay: Delay between batches in seconds
            request_timeout: Timeout for individual requests in seconds
        """
        self.base_url = base_url
        self.site_name = site_name
        self.batch_size = batch_size
        self.request_delay = request_delay
        self.request_timeout = request_timeout
        self._headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

    @abstractmethod
    async def _get_session(self) -> Any:
        """Get or create HTTP session. Must be implemented by subclass."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the HTTP session. Must be implemented by subclass."""
        pass

    @abstractmethod
    async def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a page and return its HTML content.
        Must be implemented by subclass.

        Args:
            url: URL to fetch

        Returns:
            HTML content as string or None if fetch failed
        """
        pass

    async def __aenter__(self) -> "AsyncBaseScraper":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    @abstractmethod
    async def get_listing_urls(self, max_pages: Optional[int] = None) -> List[str]:
        """
        Get URLs of all listing pages to scrape.

        Args:
            max_pages: Maximum number of pages to scrape. None for unlimited.

        Returns:
            List of listing URLs to parse
        """
        pass

    @abstractmethod
    def parse_listing(self, url: str, html: str) -> Optional[Dict]:
        """
        Parse a single listing page and extract car data.

        Args:
            url: URL of the listing
            html: HTML content of the page

        Returns:
            Dictionary with car listing data or None if parsing failed
        """
        pass

    async def fetch_page_soup(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch a page and return BeautifulSoup object.

        Args:
            url: URL to fetch

        Returns:
            BeautifulSoup object or None if fetch failed
        """
        html = await self.fetch_page(url)
        if html:
            return BeautifulSoup(html, "lxml")
        return None

    async def _fetch_and_parse_listing(self, url: str) -> Optional[Dict]:
        """
        Fetch and parse a single listing.

        Args:
            url: URL of the listing

        Returns:
            Dictionary with car listing data or None if failed
        """
        html = await self.fetch_page(url)
        if not html:
            return None

        try:
            listing_data = self.parse_listing(url, html)
            if listing_data:
                listing_data["source_url"] = url
                listing_data["source_site"] = self.site_name
            return listing_data
        except Exception as e:
            logger.error(f"Error parsing {url}: {e}")
            return None

    async def _process_batch(
        self, urls: List[str], batch_num: int, total_batches: int
    ) -> List[Dict]:
        """
        Process a batch of URLs concurrently.

        Args:
            urls: List of URLs to process
            batch_num: Current batch number (for logging)
            total_batches: Total number of batches (for logging)

        Returns:
            List of successfully parsed listings
        """
        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(urls)} URLs)")

        tasks = [self._fetch_and_parse_listing(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        listings = []
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                logger.error(f"Exception for {url}: {result}")
            elif result is not None:
                listings.append(result)

        return listings

    async def scrape_all(self, max_pages: Optional[int] = None) -> List[Dict]:
        """
        Scrape all listings from the site using async batching.

        Args:
            max_pages: Maximum number of pages to scrape for URLs

        Returns:
            List of all scraped listings
        """
        urls = await self.get_listing_urls(max_pages)
        logger.info(f"Found {len(urls)} listings to scrape from {self.site_name}")

        if not urls:
            return []

        # Split URLs into batches
        batches = [
            urls[i : i + self.batch_size] for i in range(0, len(urls), self.batch_size)
        ]
        total_batches = len(batches)

        all_listings = []

        for batch_num, batch_urls in enumerate(batches, 1):
            batch_listings = await self._process_batch(
                batch_urls, batch_num, total_batches
            )
            all_listings.extend(batch_listings)

            # Rate limiting between batches
            if batch_num < total_batches:
                await asyncio.sleep(self.request_delay)

        logger.info(
            f"Successfully scraped {len(all_listings)} listings from {self.site_name}"
        )
        return all_listings

    def scrape_all_sync(self, max_pages: Optional[int] = None) -> List[Dict]:
        """
        Synchronous wrapper for scrape_all.

        Useful for running async scraper from synchronous code.

        Args:
            max_pages: Maximum number of pages to scrape

        Returns:
            List of all scraped listings
        """
        return asyncio.run(self._run_scrape_all(max_pages))

    async def _run_scrape_all(self, max_pages: Optional[int] = 10) -> List[Dict]:
        """Run scrape_all with proper session management."""
        try:
            return await self.scrape_all(max_pages)
        finally:
            await self.close()

    # Utility methods

    def _extract_text(self, element, default: str = "") -> str:
        """Safely extract text from BeautifulSoup element."""
        if element:
            return element.get_text(strip=True)
        return default

    def _extract_number(self, text) -> Optional[float]:
        """Extract number from text (removes non-numeric chars except decimal point)."""
        if not text:
            return None

        # Handle BeautifulSoup elements
        if hasattr(text, "get_text"):
            text = text.get_text(strip=True)

        if not isinstance(text, str):
            return None

        # Remove spaces, keep numbers and decimal point
        cleaned = re.sub(r"[^\d.,]", "", text.replace(" ", ""))
        cleaned = cleaned.replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return None
