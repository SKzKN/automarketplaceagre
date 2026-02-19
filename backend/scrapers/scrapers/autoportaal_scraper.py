"""
Autoportaal.ee async scraper.

Uses AiohttpScraper for concurrent scraping.
Extracts data from JSON-LD structured data as primary source, with HTML fallback.
"""
import json
import logging
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from .aiohttp_scraper import AiohttpScraper

logger = logging.getLogger(__name__)


class AutoportaalScraper(AiohttpScraper):
    """Async scraper for autoportaal.ee."""

    auto_categories = [
        "uued-autod",
        "kasutatud-autod",
    ]

    def __init__(
        self,
        batch_size: int = 10,
        request_delay: float = 0.2,
        request_timeout: int = 30,
    ):
        """
        Initialize autoportaal scraper.

        Args:
            batch_size: Number of listings to fetch concurrently
            request_delay: Delay between batches in seconds
            request_timeout: Timeout for individual requests
        """
        super().__init__(
            base_url="https://autoportaal.ee",
            site_name="autoportaal",
            batch_size=batch_size,
            request_delay=request_delay,
            request_timeout=request_timeout,
        )

    async def get_listing_urls(self, max_pages: Optional[int] = None) -> List[str]:
        """Get URLs of all car listing pages."""
        urls = set()

        for category in self.auto_categories:
            if max_pages is None:
                # Unlimited pages - keep fetching until no more listings
                page = 1
                while True:
                    search_url = f"{self.base_url}/et/{category}"
                    if page > 1:
                        search_url = f"{search_url}?page={page}"

                    soup = await self.fetch_page_soup(search_url)
                    if not soup:
                        logger.warning(f"Could not fetch page {page}")
                        break

                    listing_links = [
                        a.attrs["href"]
                        for a in soup.select("div.advertisementsList div[id] a.dataArea")
                    ]

                    if not listing_links:
                        logger.info(f"No more listings on page {page} for category {category}")
                        break

                    urls.update(listing_links)
                    logger.info(f"Category {category}, page {page}: found {len(listing_links)} listings")
                    page += 1
            else:
                # Limited pages
                for page in range(1, max_pages + 1):
                    search_url = f"{self.base_url}/et/{category}"
                    if page > 1:
                        search_url = f"{search_url}?page={page}"

                    soup = await self.fetch_page_soup(search_url)
                    if not soup:
                        logger.warning(f"Could not fetch page {page}")
                        break

                    listing_links = [
                        a.attrs["href"]
                        for a in soup.select("div.advertisementsList div[id] a.dataArea")
                    ]

                    if not listing_links:
                        logger.info(f"No more listings on page {page} for category {category}")
                        break

                    urls.update(listing_links)
                    logger.info(f"Category {category}, page {page}: found {len(listing_links)} listings")

        urls_list = list(urls)
        logger.info(f"Total listing URLs found: {len(urls_list)}")
        return urls_list

    def _extract_json_ld(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """
        Extract JSON-LD structured data from the page.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            Parsed JSON-LD data or None if not found
        """
        try:
            # Find the Product JSON-LD script tag (usually after meta tags)
            script_tags = soup.select('script[type="application/ld+json"]')
            
            for script in script_tags:
                if script.string:
                    data = json.loads(script.string)
                    # Check if it's a Product type (car listing)
                    if isinstance(data, dict) and data.get("@type") == "Product":
                        return data
            
            # Fallback: try the last script tag pattern from the extraction script
            script_tag = soup.select("meta + script")
            if script_tag:
                last_script = script_tag[-1]
                if last_script.string:
                    try:
                        data = json.loads(last_script.string)
                        if isinstance(data, dict) and data.get("@type") == "Product":
                            return data
                    except json.JSONDecodeError:
                        pass
                        
        except (json.JSONDecodeError, AttributeError, IndexError) as e:
            logger.debug(f"Could not extract JSON-LD: {e}")
        
        return None

    def _parse_from_json_ld(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse car listing data from JSON-LD structured data.
        
        Args:
            json_data: Parsed JSON-LD data
            
        Returns:
            Dictionary with extracted car data
        """
        data = {}
        
        # Basic info
        data["title"] = json_data.get("name")
        
        # Brand/Make
        brand = json_data.get("brand", {})
        if isinstance(brand, dict):
            data["make"] = brand.get("name")
        elif isinstance(brand, str):
            data["make"] = brand
        
        # Model
        data["model"] = json_data.get("model")
        
        # Year
        year = json_data.get("modelDate") or json_data.get("vehicleModelDate")
        if year:
            try:
                data["year"] = int(year)
            except (ValueError, TypeError):
                data["year"] = None
        
        # Price from offers
        offers = json_data.get("offers", [])
        if isinstance(offers, list) and offers:
            data["price"] = offers[0].get("price")
        elif isinstance(offers, dict):
            data["price"] = offers.get("price")
        
        # Mileage
        mileage_data = json_data.get("mileageFromOdometer", {})
        if isinstance(mileage_data, dict):
            data["mileage"] = mileage_data.get("value")
        
        # Fuel type
        data["fuel_type"] = json_data.get("fuelType")
        
        # Transmission
        data["transmission"] = json_data.get("vehicleTransmission")
        
        # Body type
        data["body_type"] = json_data.get("bodyType")
        
        # Color
        data["color"] = json_data.get("color")
        
        # Description
        data["description"] = json_data.get("description")
        
        # Image (first one)
        images = json_data.get("image", [])
        if isinstance(images, list) and images:
            data["image_url"] = images[0]
        elif isinstance(images, str):
            data["image_url"] = images
        
        return data

    def _parse_from_html(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Parse car listing data from HTML (fallback method).
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            Dictionary with extracted car data
        """
        data = {}
        
        # Extract title
        title_elem = soup.select_one("h1#vehicleTitle")
        data["title"] = self.extract_text(title_elem) or None

        # Extract price
        price_elem = soup.select_one("div.currentPrice table tr td:first-child")
        data["price"] = self.extract_number(price_elem)

        # Extract make and model from title
        if data["title"]:
            parts = data["title"].split()
            if len(parts) >= 2:
                data["make"] = parts[0]
                data["model"] = " ".join(parts[1:-1]) if len(parts) > 2 else parts[1]
                if parts[-1].isdigit() and len(parts[-1]) == 4:
                    data["year"] = int(parts[-1])

        # Extract technical data from tables
        rows = soup.select("h1 + table > tr + tr") + soup.select(
            "div.technicalDataBlock table tr"
        )
        
        for row in rows:
            cells = row.select("td")
            if len(cells) >= 2:
                header = self.extract_text(cells[0])
                value = self.extract_text(cells[1])

                if "Läbisõit" in header:
                    data["mileage"] = self.extract_number(value)
                elif "Kütus" in header:
                    data["fuel_type"] = value
                elif "Käigukast" in header:
                    data["transmission"] = value
                elif "Keretüüp" in header:
                    data["body_type"] = value
                elif "Värv" in header:
                    data["color"] = value

        # Extract image
        img_elem = soup.select_one("div.mainImage img")
        if img_elem and img_elem.get("src"):
            data["image_url"] = img_elem["src"]

        # Extract description
        desc_elem = soup.select_one("div.descriptionBlock")
        if desc_elem:
            data["description"] = self.extract_text(desc_elem) or None

        return data

    def _merge_data(self, json_data: Dict[str, Any], html_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge JSON-LD data with HTML data, preferring JSON-LD values.
        
        Args:
            json_data: Data extracted from JSON-LD
            html_data: Data extracted from HTML
            
        Returns:
            Merged dictionary with all available data
        """
        merged = {}
        
        # All possible fields
        all_keys = set(json_data.keys()) | set(html_data.keys())
        
        for key in all_keys:
            json_val = json_data.get(key)
            html_val = html_data.get(key)
            
            # Prefer JSON-LD value if present and not empty
            if json_val is not None and json_val != "" and json_val != []:
                merged[key] = json_val
            elif html_val is not None and html_val != "" and html_val != []:
                merged[key] = html_val
            else:
                merged[key] = None
        
        return merged

    def parse_listing(self, url: str, html: str) -> Optional[Dict]:
        """
        Parse a single autoportaal listing.
        
        First extracts data from JSON-LD structured data, then supplements
        with HTML parsing for any missing fields.
        
        Args:
            url: URL of the listing
            html: HTML content of the page
            
        Returns:
            Dictionary with car listing data or None if parsing failed
        """
        try:
            soup = BeautifulSoup(html, "lxml")
            
            # Try to extract from JSON-LD first
            json_ld = self._extract_json_ld(soup)
            
            if json_ld:
                json_data = self._parse_from_json_ld(json_ld)
                logger.debug(f"Extracted {len([v for v in json_data.values() if v])} fields from JSON-LD")
            else:
                json_data = {}
                logger.debug("No JSON-LD found, using HTML only")
            
            # Always parse HTML as fallback
            html_data = self._parse_from_html(soup)
            
            # Merge data (JSON-LD takes priority)
            result = self._merge_data(json_data, html_data)
            
            # Return only fields defined in the domain entity
            return {
                "title": result.get("title"),
                "make": result.get("make"),
                "model": result.get("model"),
                "year": result.get("year"),
                "price": result.get("price"),
                "mileage": result.get("mileage"),
                "fuel_type": result.get("fuel_type"),
                "transmission": result.get("transmission"),
                "body_type": result.get("body_type"),
                "color": result.get("color"),
                "description": result.get("description"),
                "image_url": result.get("image_url"),
            }

        except Exception as e:
            logger.error(f"Error parsing Autoportaal listing {url}: {e}")
            return None
