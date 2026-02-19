"""
Base scraper class for all car listing scrapers.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

import logging
import re
import time

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base class for all car listing scrapers."""
    
    def __init__(self, base_url: str, site_name: str):
        self.base_url = base_url
        self.site_name = site_name
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    @abstractmethod
    def get_listing_urls(self, max_pages: int = 10) -> List[str]:
        """Get URLs of all listing pages to scrape."""
        pass
    
    @abstractmethod
    def parse_listing(self, url: str) -> Optional[Dict]:
        """Parse a single listing page and extract car data."""
        pass
    
    def scrape_all(self, max_pages: int = 10) -> List[Dict]:
        """Scrape all listings from the site."""
        listings = []
        urls = self.get_listing_urls(max_pages)
        
        logger.info(f"Found {len(urls)} listings to scrape from {self.site_name}")
        
        for i, url in enumerate(urls, 1):
            try:
                logger.info(f"[{i}/{len(urls)}] Scraping listing: {url}")
                listing_data = self.parse_listing(url)
                if listing_data:
                    listing_data['source_url'] = url
                    listing_data['source_site'] = self.site_name
                    listings.append(listing_data)
                
                # Be respectful with rate limiting
                if i % 10 == 0:
                    time.sleep(2)
                else:
                    time.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"Error scraping {url}: {str(e)}")
                continue
        
        logger.info(f"Successfully scraped {len(listings)} listings from {self.site_name}")
        return listings
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a page."""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'lxml')
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None
    
    def extract_text(self, element, default: str = "") -> str:
        """Safely extract text from BeautifulSoup element."""
        if element:
            return element.get_text(strip=True)
        return default
    
    def extract_number(self, text) -> Optional[float]:
        """Extract number from text (removes non-numeric chars except decimal point)."""
        if not text:
            return None
        
        # Handle BeautifulSoup elements
        if hasattr(text, 'get_text'):
            text = text.get_text(strip=True)
        
        if not isinstance(text, str):
            return None
            
        # Remove spaces, keep numbers and decimal point
        cleaned = re.sub(r'[^\d.,]', '', text.replace(' ', ''))
        cleaned = cleaned.replace(',', '.')
        try:
            return float(cleaned)
        except:
            return None
