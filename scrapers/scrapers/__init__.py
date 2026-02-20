"""
Scrapers package - contains all website-specific scraper implementations.
"""
from .base_scraper import BaseScraper
from .async_base_scraper import AsyncBaseScraper
from .aiohttp_scraper import AiohttpScraper
from .curl_cffi_scraper import CurlCffiScraper
from .auto24_scraper import Auto24Scraper
from .autodiiler_scraper import AutoDiilerScraper
from .veego_scraper import VeegoScraper
from .okidoki_scraper import OkidokiScraper
from .autoportaal_scraper import AutoportaalScraper

__all__ = [
    "BaseScraper",
    "AsyncBaseScraper",
    "AiohttpScraper",
    "CurlCffiScraper",
    "Auto24Scraper",
    "AutoDiilerScraper",
    "VeegoScraper",
    "OkidokiScraper",
    "AutoportaalScraper",
]
