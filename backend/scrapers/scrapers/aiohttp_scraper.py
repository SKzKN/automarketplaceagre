import asyncio
import logging
from typing import Any, Dict, Optional

import aiohttp

from .async_base_scraper import AsyncBaseScraper

logger = logging.getLogger(__name__)


class AiohttpScraper(AsyncBaseScraper):
    """
    Async scraper using aiohttp for HTTP requests.

    Standard HTTP client suitable for sites without Cloudflare protection.
    """

    def __init__(
        self,
        base_url: str,
        site_name: str,
        batch_size: int = 10,
        request_delay: float = 0.5,
        request_timeout: int = 30,
    ):
        super().__init__(
            base_url, site_name, batch_size, request_delay, request_timeout
        )
        self._session: aiohttp.ClientSession = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""

        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.request_timeout)
            self._session = aiohttp.ClientSession(
                headers=self._headers,
                timeout=timeout,
            )
        return self._session

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a page and return its HTML content.

        Args:
            url: URL to fetch

        Returns:
            HTML content as string or None if fetch failed
        """
        try:
            session = await self._get_session()
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"Got status {response.status} for {url}")
                    return None
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching {url}")
            return None
        except aiohttp.ClientError as e:
            logger.error(f"Client error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            return None

    async def _post_json(
        self, url: str, json_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Make a POST request with JSON data and return parsed JSON response."""
        try:
            session = await self._get_session()
            headers = {**self._headers, "Content-Type": "application/json"}
            async with session.post(url, json=json_data, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"Got status {response.status} for POST {url}")
                    return None
        except Exception as e:
            logger.error(f"Error making POST request to {url}: {e}")
            return None
