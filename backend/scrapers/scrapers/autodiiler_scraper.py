import json
import logging
import re
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from .aiohttp_scraper import AiohttpScraper

import asyncio

logger = logging.getLogger(__name__)


class AutoDiilerScraper(AiohttpScraper):
    """Async scraper for autodiiler.ee."""

    def __init__(
        self,
        batch_size: int = 10,
        request_delay: float = 1.0,
        request_timeout: int = 30,
    ):
        super().__init__(
            base_url="https://autodiiler.ee",
            site_name="autodiiler",
            batch_size=batch_size,
            request_delay=request_delay,
            request_timeout=request_timeout,
        )

    async def _get_makes(self) -> List[str]:
        try:
            soup = await self.fetch_page_soup(f"{self.base_url}/et")
            if not soup:
                logger.error("Failed to fetch homepage for makes extraction")
                return []
            
            makes_options = soup.select("div#home-search-brand-id-dropdown ul li")
            makes = []

            for make_option in makes_options:
                make_id = int(make_option.attrs["id"].replace("home-search-brand-id-multiselect-option-", "").strip())
                makes.append(make_id)

            return makes
        except Exception as e:
            logger.error(f"Error fetching makes: {e}")
            return []
        
    async def _get_models(self, make_id: int) -> list[tuple[int, str | None, int]]:
        try:
            response = await self.fetch_page(f"https://garage.autodiiler.ee/api/v1/vehicles/misc/brands/{make_id}/models?locale=et&vehicle_type_id=")
            if response is None:
                logger.error(f"Failed to fetch models for make {make_id}")
                return []
            
            items = json.loads(response)["data"]
            
            if not isinstance(items, list):
                logger.error(f"Unexpected format for make (series/models) {make_id}: {items}")
                return []
            logger.info(f"Fetched {len(items)} (series/models) for make {make_id}")

            results = []
            for item in items:
                series_label = item.get("label", None)
                for model in item.get("options", []):
                    results.append((make_id, series_label, model.get("value")))

            return results
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding models JSON for make {make_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching models for make {make_id}: {e}")
            return []
        
    async def build_make_series_model(self) -> List[tuple[str, str | None, str]]:
        """Build make, series, model lookup."""
        makes = await self._get_makes()

        # Step 1: Fetch all models for all makes concurrently
        async def get_make_with_models(make_id: Dict[str, Any]) -> List[Dict[str, Any]]:
            return await self._get_models(make_id=make_id)

        make_tasks = [get_make_with_models(make_id) for make_id in makes]
        results = await asyncio.gather(*make_tasks, return_exceptions=True)

        make_series_models = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Exception during make/model fetching: {result}")
            else:
                make_series_models.extend(result)
        logger.info(f"Built total of {len(make_series_models)} make/series/model combinations")

        return make_series_models
        
    async def get_listings_make_series_model(self, make_series_model: tuple[str, str | None, str]) -> list[tuple[str, tuple[str, str | None, str]]]:
        """Get listings for a specific make/series/model."""
        listings_urls = set()
        page = 1
        search_url = "https://garage.autodiiler.ee/api/v1/vehicles?locale=et&page={page}&ba={make_id}&bm={model_id}&s=default"
        while True:
            try:
                logger.info(search_url.format(page=page, make_id=make_series_model[0], model_id=make_series_model[2]))
                response = await self.fetch_page(search_url.format(page=page, make_id=make_series_model[0], model_id=make_series_model[2]))
                
                if not response:
                    logger.warning(f"Could not fetch page {page} for make/series/model {make_series_model}")
                    break

                data = json.loads(response)
                listings = data["data"]

                if not listings:
                    logger.info(f"No more listings on page {page} for make/series/model {make_series_model}")
                    break
                
                for listing in listings:
                    listing_url = f"{self.base_url}/et/vehicles/{listing['id']}"
                    listings_urls.add((listing_url, make_series_model))
                logger.info(f"Page {page} for make/series/model {make_series_model}: found {len(listings)} listings")
                page += 1
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding listings JSON for make/series/model {make_series_model} on page {page}: {e}")
                break
            except Exception as e:
                logger.error(f"Unexpected error parsing listings for make/series/model {make_series_model} on page {page}: {e}")
                break
        return list(listings_urls)
    
    async def process_get_listings_make_series_model_batch(self, make_series_models: List[tuple[str, str | None, str]]) -> List[tuple[str, tuple[str, str | None, str]]]:
        """Process a batch of make/series/models to get their listings."""
        tasks = [
            self.get_listings_make_series_model(make_series_model)
            for make_series_model in make_series_models
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        listings_urls = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Exception during batch listing URL fetching: {result}")
            else:
                listings_urls.extend(result)
        return listings_urls

    
    async def get_listing_urls(self, max_pages: Optional[int] = None) -> List[tuple]:
        """Get URLs of all car listing pages."""
        urls_list = []

        make_series_models = await self.build_make_series_model()
        logger.info(f"Starting URL extraction for {len(make_series_models)} make/series/model combinations")

        successful_calls = 0
        failed_calls = 0
        total_urls = 0

        # Process in batches to avoid overwhelming the server
        for i in range(0, len(make_series_models), self.batch_size):
            batch = make_series_models[i : i + self.batch_size]
            results = await self.process_get_listings_make_series_model_batch(batch)
            
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Exception during batch processing: {result}")
                    failed_calls += 1
                else:
                    successful_calls += 1
                    total_urls += len(result)
                    urls_list.extend([result])

            if max_pages and len(urls_list) >= max_pages * 10:  # Safety check to prevent runaway scraping
                logger.warning(f"Reached max_pages limit ({max_pages * 10} URLs). Stopping URL extraction.")
                break


            # Extended rate limiting every 30 batches
            if (i // self.batch_size) % 30 == 0 and i != 0:
                await asyncio.sleep(self.request_delay * 5)

            # Rate limiting between batches
            elif (i + self.batch_size) < len(make_series_models):
                await asyncio.sleep(self.request_delay)

        logger.info(f"URL extraction complete: {successful_calls} successful calls, "
                    f"{failed_calls} failed calls, {total_urls} total URLs extracted")
        
        return urls_list

    async def _fetch_and_parse_listing(self, url: str, make_model_series: tuple[str, str | None, str]) -> Optional[Dict]:
        html = await self.fetch_page(url)
        if not html:
            return None

        try:
            listing_data = self.parse_listing(url, html)
            if listing_data:
                listing_data["series"] = make_model_series[1]
                listing_data["source_url"] = url
                listing_data["source_site"] = self.site_name
                listing_data["source_taxonomy"] = {
                    "make_id": make_model_series[0],
                    "model_id": make_model_series[2],
                    "series_id": None
                }
            return listing_data
        except Exception as e:
            logger.error(f"Error parsing {url}: {e}")
            return None
        
    async def _process_batch(self, urls: List[tuple[str, tuple[str, str | None, str]]], batch_num: int, total_batches: int) -> List[Dict]:
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

        tasks = [self._fetch_and_parse_listing(url, make_model_series) for url, make_model_series in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        listings = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Exception during listing parsing: {result}")
            elif result is not None:
                listings.append(result)
        
        return listings

    def _extract_json_ld(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """
        Extract JSON-LD structured data from the page.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            Parsed JSON-LD data or None if not found
        """
        try:
            scripts = soup.find_all("script", type="application/ld+json")

            for script in scripts:
                if script.string:
                    data = json.loads(script.string)

                    if isinstance(data, dict):
                        if "@graph" in data:
                            for item in data["@graph"]:
                                item_types = item.get("@type", [])
                                if not isinstance(item_types, list):
                                    item_types = [item_types]

                                if any(t in ["Product", "Car", "Vehicle"] for t in item_types):
                                    return item
                        elif data.get("@type") in ["Product", "Car", "Vehicle"]:
                            return data

        except (json.JSONDecodeError, AttributeError) as e:
            logger.warning(f"Could not extract JSON-LD: {e}")
            return None

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

        # Title/Name
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
        year = json_data.get("vehicleModelDate") or json_data.get("modelDate") or json_data.get("dateVehicleFirstRegistered")
        if year:
            try:
                year_match = re.search(r"\b(19|20)\d{2}\b", str(year))
                if year_match:
                    data["year"] = int(year_match.group())
            except (ValueError, TypeError):
                data["year"] = None

        # Price from offers
        offers = json_data.get("offers", {})
        if isinstance(offers, list) and offers:
            offers = offers[0]
        if isinstance(offers, dict):
            price = offers.get("price")
            if price:
                try:
                    data["price"] = float(str(price).replace(" ", "").replace(",", ""))
                except (ValueError, TypeError):
                    data["price"] = None

        # Mileage from description or mileageFromOdometer
        mileage_data = json_data.get("mileageFromOdometer", {})
        if isinstance(mileage_data, dict):
            data["mileage"] = mileage_data.get("value")
        else:
            # Try to extract from description
            desc = json_data.get("description", "")
            if desc and "km" in desc.lower():
                for part in desc.split("|"):
                    if "km" in part.lower():
                        km_match = re.search(r"(\d[\d\s]+)", part)
                        if km_match:
                            km_str = km_match.group(1).replace("\xa0", "").replace(" ", "")
                            try:
                                data["mileage"] = float(km_str)
                            except ValueError:
                                pass
                            break

        # Fuel type
        data["fuel_type"] = json_data.get("fuelType") or json_data.get("engineType")

        # Transmission
        data["transmission"] = json_data.get("vehicleTransmission")

        # Body type
        data["body_type"] = json_data.get("bodyType")

        # Color
        data["color"] = json_data.get("color")

        # Description
        data["description"] = json_data.get("description")

        # Image
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
        title_elem = soup.find("h1")
        data["title"] = self._extract_text(title_elem) or None

        # Extract make and model from title
        if data["title"]:
            parts = data["title"].split()
            if len(parts) >= 2:
                data["make"] = parts[0]
                model_parts = []
                for i, part in enumerate(parts[1:], 1):
                    if part.isdigit() and len(part) == 4:
                        break
                    if i > 1 and "kw" in part.lower():
                        break
                    model_parts.append(part)
                if model_parts:
                    data["model"] = " ".join(model_parts)

        # Extract price from text
        all_text = soup.get_text()
        price_pattern = re.compile(r"(\d{1,3}(?:\s?\d{3})*)\s*€")
        prices = price_pattern.findall(all_text)
        if prices:
            valid_prices = []
            for p in prices:
                p_clean = p.replace("\xa0", "").replace(" ", "")
                try:
                    p_val = float(p_clean)
                    if 100 <= p_val <= 500000:
                        valid_prices.append(p_val)
                except ValueError:
                    pass
            if valid_prices:
                data["price"] = max(valid_prices)

        # Extract description
        desc_elem = soup.find("div", class_=re.compile(r"description|desc|content"))
        if desc_elem:
            description = self._extract_text(desc_elem)
            if description and len(description) > 2000:
                description = description[:2000]
            data["description"] = description

        # Extract image
        for img in soup.find_all("img", src=True):
            src = img.get("src", "") or img.get("data-src", "")
            if src and "media.autodiiler.ee" in src:
                if not any(skip in src.lower() for skip in ["logo", "icon", "flag"]):
                    data["image_url"] = src
                    break

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
        all_keys = set(json_data.keys()) | set(html_data.keys())

        for key in all_keys:
            json_val = json_data.get(key)
            html_val = html_data.get(key)

            if json_val is not None and json_val != "" and json_val != []:
                merged[key] = json_val
            elif html_val is not None and html_val != "" and html_val != []:
                merged[key] = html_val
            else:
                merged[key] = None

        return merged

    def parse_listing(self, url: str, html: str) -> Optional[Dict]:
        """
        Parse a single autodiiler listing.

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
            else:
                json_data = {}
                logger.info("No JSON-LD found, using HTML only")

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
            logger.error(f"Error parsing AutoDiiler listing {url}: {e}")
            return None
