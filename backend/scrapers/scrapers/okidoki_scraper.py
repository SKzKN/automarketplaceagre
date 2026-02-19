"""
Okidoki.ee scraper - cars/vehicles category only.
"""
from typing import Dict, List, Optional

import logging
import re

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class OkidokiScraper(BaseScraper):
    """Scraper for okidoki.ee - cars/vehicles category only."""
    
    def __init__(self):
        super().__init__("https://www.okidoki.ee", "okidoki")
        self.car_category = "auto"
    
    def get_listing_urls(self, max_pages: int = 10) -> List[str]:
        """Get URLs of all car listing pages from okidoki.ee."""
        urls = []
        
        for page in range(1, max_pages + 1):
            search_url = f"{self.base_url}/browse/kat_0/q_auto/page_{page}.html"
            
            alt_urls = [
                f"{self.base_url}/auto?page={page}",
                f"{self.base_url}/category/auto?page={page}",
                f"{self.base_url}/browse/auto?page={page}"
            ]
            
            soup = None
            for url_pattern in [search_url] + alt_urls:
                soup = self.fetch_page(url_pattern)
                if soup:
                    break
            
            if not soup:
                break
            
            listing_links = soup.find_all('a', href=re.compile(r'/item/\d+|/auto/\d+|/listing/\d+'))
            
            if not listing_links:
                listing_links = soup.find_all('a', class_=re.compile(r'item|listing|product'))
            
            if not listing_links:
                break
            
            for link in listing_links:
                href = link.get('href')
                if href:
                    href_lower = href.lower()
                    if any(keyword in href_lower for keyword in ['auto', 'car', 'vehicle', 'sõiduk']):
                        full_url = self.base_url + href if href.startswith('/') else href
                        if full_url not in urls:
                            urls.append(full_url)
            
            next_link = soup.find('a', class_=re.compile(r'next|pagination'))
            if not next_link or page >= max_pages:
                break
        
        return urls
    
    def parse_listing(self, url: str) -> Optional[Dict]:
        """Parse a single okidoki.ee listing."""
        soup = self.fetch_page(url)
        if not soup:
            return None
        
        try:
            # Verify this is a car listing
            page_text = soup.get_text().lower()
            if not any(keyword in page_text for keyword in ['auto', 'car', 'sõiduk', 'vehicle']):
                return None
            
            # Extract title
            title_elem = soup.find('h1') or soup.find('title')
            title = self.extract_text(title_elem)
            
            # Extract price
            price_elem = soup.find('span', class_=re.compile(r'price')) or soup.find('div', class_=re.compile(r'price'))
            price = None
            if price_elem:
                price_text = self.extract_text(price_elem)
                price = self.extract_number(price_text)
            
            # Extract make and model
            make = None
            model = None
            year = None
            
            if title:
                parts = title.split()
                if len(parts) >= 2:
                    make = parts[0]
                    model = ' '.join(parts[1:-1]) if len(parts) > 2 else parts[1]
                    if parts[-1].isdigit() and len(parts[-1]) == 4:
                        year = int(parts[-1])
            
            # Extract details
            details = {}
            detail_sections = soup.find_all('div', class_=re.compile(r'detail|spec|attribute|info'))
            for section in detail_sections:
                items = section.find_all('div') or section.find_all('tr')
                for item in items:
                    label_elem = item.find('span', class_=re.compile(r'label|key|name'))
                    value_elem = item.find('span', class_=re.compile(r'value|data|content'))
                    if label_elem and value_elem:
                        label = self.extract_text(label_elem).lower()
                        value = self.extract_text(value_elem)
                        details[label] = value
            
            if not make and 'mark' in details:
                make = details['mark']
            if not model and 'mudel' in details:
                model = details['mudel']
            if not year and 'aasta' in details:
                year_text = details['aasta']
                year_match = re.search(r'\d{4}', year_text)
                if year_match:
                    year = int(year_match.group())
            
            mileage = None
            if 'läbisõit' in details or 'km' in details:
                mileage_text = details.get('läbisõit') or details.get('km')
                mileage = self.extract_number(mileage_text)
            
            fuel_type = details.get('kütus')
            transmission = details.get('käigukast')
            body_type = details.get('keretüüp')
            color = details.get('värv')
            
            # Extract description
            desc_elem = soup.find('div', class_=re.compile(r'description|desc|content|text'))
            description = self.extract_text(desc_elem)
            
            # Extract image
            image_url = None
            img_elem = soup.find('img', class_=re.compile(r'main|primary|featured|gallery'))
            if img_elem:
                image_url = img_elem.get('src') or img_elem.get('data-src')
                if image_url and image_url.startswith('/'):
                    image_url = self.base_url + image_url
            
            return {
                'title': title,
                'make': make,
                'model': model,
                'year': year,
                'price': price,
                'mileage': mileage,
                'fuel_type': fuel_type,
                'transmission': transmission,
                'body_type': body_type,
                'color': color,
                'description': description,
                'image_url': image_url
            }
            
        except Exception as e:
            logger.error(f"Error parsing okidoki listing {url}: {str(e)}")
            return None
