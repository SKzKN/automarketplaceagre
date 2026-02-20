"""
Scrapers module for car marketplace aggregator.

This module provides web scrapers for various Estonian car marketplace websites.
It includes both synchronous (BaseScraper) and asynchronous (AsyncBaseScraper) implementations.

Usage:
    # Run all scrapers via command line
    python -m scrapers.main
    
    # Or import individual scrapers
    from scrapers.scrapers import AutoportaalScraper, Auto24Scraper
"""
from .scrapers import (
    BaseScraper,
    AsyncBaseScraper,
    Auto24Scraper,
    AutoDiilerScraper,
    VeegoScraper,
    OkidokiScraper,
    AutoportaalScraper,
)
from .config import ScraperConfig, get_config
from .repository import ScraperRepository

__all__ = [
    # Base classes
    "BaseScraper",
    "AsyncBaseScraper",
    # Scrapers
    "Auto24Scraper",
    "AutoDiilerScraper",
    "VeegoScraper",
    "OkidokiScraper",
    "AutoportaalScraper",
    # Config & Repository
    "ScraperConfig",
    "get_config",
    "ScraperRepository",
]
