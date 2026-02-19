import asyncio
import logging
from typing import Any, Optional

import curl_cffi

from .async_base_scraper import AsyncBaseScraper

logger = logging.getLogger(__name__)


class CurlCffiScraper(AsyncBaseScraper):
    """
    Async scraper using curl_cffi for HTTP requests with browser impersonation.

    Bypasses Cloudflare protection by impersonating real browser TLS fingerprints.
    Use this for sites with Cloudflare or similar bot protection.
    """

    def __init__(
        self,
        base_url: str,
        site_name: str,
        batch_size: int = 5,  # Lower default for CF-protected sites
        request_delay: float = 1.0,  # Higher default delay
        request_timeout: int = 30,
        impersonate: str = "chrome",
        max_retries: int = 3,
    ):
        """
        Initialize curl_cffi scraper.

        Args:
            base_url: Base URL of the website
            site_name: Name of the website for logging
            batch_size: Number of requests to process concurrently
            request_delay: Delay between batches in seconds
            request_timeout: Timeout for individual requests
            impersonate: Browser to impersonate (chrome, firefox, safari, etc.)
            max_retries: Number of retries on 403/timeout errors
        """
        super().__init__(
            base_url, site_name, batch_size, request_delay, request_timeout
        )
        self._session: Any = None
        self.impersonate = impersonate
        self.max_retries = max_retries

    async def _get_session(self) -> curl_cffi.AsyncSession:
        """Get or create curl_cffi async session."""
        if self._session is None:
            self._session = curl_cffi.AsyncSession(
                impersonate=self.impersonate,
                timeout=self.request_timeout,
            )
        return self._session

    async def close(self) -> None:
        """Close the curl_cffi session."""
        if self._session:
            await self._session.close()
            self._session = None

    async def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a page with Cloudflare bypass and retry logic.

        Args:
            url: URL to fetch

        Returns:
            HTML content as string or None if fetch failed
        """
        for attempt in range(self.max_retries):
            try:
                session = await self._get_session()
                response = await session.get(url)
                response.raise_for_status()

                if response.status_code == 200:
                    return response.text
                elif response.status_code == 403:
                    logger.warning(
                        f"Got 403 for {url}, attempt {attempt + 1}/{self.max_retries}"
                    )
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2 * (attempt + 1))
                        continue
                else:
                    logger.warning(f"Got status {response.status_code} for {url}")
                    return None
            except curl_cffi.requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error fetching {url}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 * (attempt + 1))
                    continue
            except curl_cffi.requests.exceptions.Timeout:
                logger.error(f"Timeout fetching {url}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2)
                    continue
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2)
                    continue

        return None
