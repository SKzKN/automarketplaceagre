import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from .aiohttp_scraper import AiohttpScraper

logger = logging.getLogger(__name__)


class VeegoTranslator:
    # Matches entries like:
    # series:{t:0,b:{t:2,i:[{t:3}],s:"seeria"}}
    # "1 series":{t:0,b:{t:2,i:[{t:3}],s:"1 seeria"}}
    _ENTRY_RE = re.compile(
        r'(?:^|,)(?:"((?:\\.|[^"\\])*)"|([A-Za-z_$][\w$]*)):\{t:0,b:\{t:2,i:\[\{t:3\}\],s:"((?:\\.|[^"\\])*)"\}\}'
    )

    def __init__(self, mapping: Dict[str, str]):
        self.mapping = mapping

    @classmethod
    def from_js_string(cls, js_string: str) -> "VeegoTranslator":
        mapping: Dict[str, str] = {}
        for m in cls._ENTRY_RE.finditer(js_string):
            key = m.group(1) or m.group(2)  # quoted key or bare identifier key
            val = m.group(3)
            mapping[key] = val

        if not mapping:
            raise ValueError("No translations found. Pattern may have changed in the Nuxt chunk.")

        return cls(mapping)

    def t(self, text: str, *, no_translate: bool = False) -> str:
        """
        Translate a label. If `no_translate=True`, returns input unchanged.
        Strategy:
          1) Exact dictionary match
          2) Special-case 'series' with number in either order
          3) Fallback: replace standalone word 'series' if we know its translation
        """
        if no_translate:
            return text

        # 1) exact hit
        direct = self.mapping.get(text)
        if direct is not None:
            return direct

        # 2) normalize “1 series” or “series 1”
        series_et = self.mapping.get("series")
        if series_et:
            m1 = re.fullmatch(r"\s*(\d+)\s+series\s*", text, flags=re.IGNORECASE)
            if m1:
                return f"{m1.group(1)} {series_et}"

            m2 = re.fullmatch(r"\s*series\s+(\d+)\s*", text, flags=re.IGNORECASE)
            if m2:
                return f"{series_et} {m2.group(1)}"

            # 3) replace word boundary series -> seeria
            replaced = re.sub(r"\bseries\b", series_et, text, flags=re.IGNORECASE)
            if replaced != text:
                return replaced

        # no translation known
        return text


class VeegoScraper(AiohttpScraper):
    """Async scraper for veego.ee using public API for vehicle IDs."""

    def __init__(
        self,
        batch_size: int = 10,
        request_delay: float = 0.3,
        request_timeout: int = 30,
    ):
        """
        Initialize Veego scraper.

        Args:
            batch_size: Number of listings to fetch concurrently
            request_delay: Delay between batches in seconds
            request_timeout: Timeout for individual requests
        """
        super().__init__(
            base_url="https://veego.ee",
            site_name="veego",
            batch_size=batch_size,
            request_delay=request_delay,
            request_timeout=request_timeout,
        )
        self.api_base = "https://api.veego.ee/api/"
        self.translator = None
        self.models_lookup: Dict[str, str] = {}
        self.unique_sub_models: List[str] = []

    async def _get_makes(self) -> List[str]:
        """Get all vehicle model IDs for a given make from the public API."""
        try:
            api_url = f"{self.api_base}/attr/vehicles/makes?top=false&all=true"
            logger.info(f"Fetching vehicle makes from API: {api_url}")
            response = await self.fetch_page(api_url)

            if response is None:
                logger.error(f"Failed to fetch vehicle makes from API: {api_url}")
                return []

            makes = json.loads(response)

            if not isinstance(makes, list):
                logger.error("Unexpected API response format")
                return []
            
            make_ids = []

            for make in makes:
                make_ids.append(make["id"])
            return make_ids
        
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from API")
            return []

        except Exception as e:
            logger.error(f"Error getting vehicle makes from API {api_url}: {e}")
            return []
        
    async def _get_models(self, make_id: str) -> List[tuple[str, str | None, str]]:
        """Get all vehicle model IDs from the public API."""
        try:
            api_url = f"{self.api_base}attr/{make_id}/models"
            logger.info(f"Fetching vehicle models for make {make_id} from API: {api_url}")
            response = await self.fetch_page(api_url)

            if response is None:
                logger.error(f"Failed to fetch vehicle models for make {make_id} from API: {api_url}")
                return []

            items = json.loads(response)


            if not isinstance(items, list):
                logger.error("Unexpected API response format")
                return []
            
            results = []
            for item in items:
                if item["lvl"] == 1:
                    if len(item.get("models", [])) != 0:
                        series_id = item["id"]
                        for model in item.get("models", []):
                            results.append((make_id, series_id, model["id"]))
                    else:
                        results.append((make_id, None, item["id"]))

            return results
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from API")
            return []
        except Exception as e:
            logger.error(f"Error getting vehicle model IDs from API {api_url}: {e}")
            return []
        
    async def build_make_series_model(self) -> List[tuple[str, str | None, str]]:
        """Build a list of all make/series/model combinations."""
        make_ids = await self._get_makes()

        async def fetch_models_for_make(make_id: str):
            return await self._get_models(make_id)

        tasks = [fetch_models_for_make(mid) for mid in make_ids]
        results = await asyncio.gather(*tasks)

        make_series_models = []
        for result in results:
            if result is None:
                continue
            if isinstance(result, Exception):
                logger.error(f"Error fetching models: {result}")
            else:
                make_series_models.extend(result)

        return make_series_models
    
    async def get_listings_make_series_model(self, make_series_model: tuple[str, str | None, str], max_pages: Optional[int] = None) -> list[tuple[str, tuple[str, str | None, str]]]:
        listing_urls = set()

        if max_pages is None:
            page = 1
            api_url = "https://api.veego.ee/api/v2/search"
            while True:
                try:
                    json_payload ={
                        "make_id": make_series_model[0],
                        "model_ids": [
                            make_series_model[2]
                        ],
                        "is_new": 0,
                        "per_page": 30,
                        "page": page,
                        "order_by": "Standard"
                    }
                    response = await self._post_json(api_url, json_data=json_payload)

                    if response is None:
                        logger.error(f"Failed to fetch listing URLs for {api_url} with payload {json_payload}")
                        break

                    listings = response["results"]

                    if not listings:
                        logger.info(f"No more listings found for {api_url} with payload {json_payload} at page {page}")
                        break

                    for listing in listings:
                        listing_id = listing["id"]
                        url = f"{self.base_url}/soidukid/{listing_id}"
                        listing_urls.add((url, make_series_model))

                    logger.info(f"Fetched {len(listings)} listings for {api_url} with payload {json_payload} at page {page}")
                    page += 1
                except Exception as e:
                    logger.error(f"Error fetching listings for {api_url} with payload {json_payload} at page {page}: {e}")
                    break
        else:
            for page in range(1, max_pages + 1):
                try:
                    api_url = "https://api.veego.ee/api/v2/search"
                    json_payload ={
                        "make_id": make_series_model[0],
                        "model_ids": [
                            make_series_model[2]
                        ],
                        "is_new": 0,
                        "per_page": 30,
                        "page": page,
                        "order_by": "Standard"
                    }
                    response = await self._post_json(api_url, json_data=json_payload)

                    if response is None:
                        logger.error(f"Failed to fetch listing URLs for {api_url} with payload {json_payload}")
                        break

                    listings = response["results"]

                    if not listings:
                        logger.info(f"No more listings found for {api_url} with payload {json_payload} at page {page}")
                        break

                    for listing in listings:
                        listing_id = listing["id"]
                        url = f"{self.base_url}/soidukid/{listing_id}"
                        listing_urls.add((url, make_series_model))

                    logger.info(f"Fetched {len(listings)} listings for {api_url} with payload {json_payload} at page {page}")
                except Exception as e:
                    logger.error(f"Error fetching listings for {api_url} with payload {json_payload} at page {page}: {e}")
                    break

        return list(listing_urls)

    async def process_get_listings_make_series_model_batch(self, make_series_models: List[tuple[str, str | None, str]], max_pages: Optional[int] = None) -> List[tuple[str, tuple[str, str | None, str]]]:
        """Process a batch of make/series/models to get their listings."""
        tasks = [
            self.get_listings_make_series_model(make_series_model, max_pages=max_pages)
            for make_series_model in make_series_models
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        listings_urls = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Exception during batch listing URL fetching: {result}")
                return []
            else:
                listings_urls.append(result)
        return listings_urls

    
    async def get_listing_urls(self, max_pages: Optional[int] = None) -> List[tuple]:
        """Get URLs of all car listing pages."""
        urls_list = []

        successful_calls = 0
        failed_calls = 0
        total_urls = 0

        make_series_models = await self.build_make_series_model()
        logger.info(f"Starting URL extraction for {len(make_series_models)} make/series/model combinations")

        # Process in batches to avoid overwhelming the server
        for i in range(0, len(make_series_models), self.batch_size):
            batch = make_series_models[i : i + self.batch_size]
            results = await self.process_get_listings_make_series_model_batch(batch, max_pages=max_pages)
            
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Exception during batch processing: {result}")
                    failed_calls += 1
                else:
                    successful_calls += 1
                    total_urls += len(result)
                    urls_list.extend(result) 

            if max_pages and total_urls >= max_pages * 10:  # Safety check to prevent runaway scraping
                logger.warning(f"Reached max_pages limit ({max_pages * 10} URLs) during listing URL extraction. Stopping further API calls.")
                break

            # Extended rate limiting every 30 batches
            if (i // self.batch_size) % 30 == 0 and i != 0:
                await asyncio.sleep(self.request_delay * 5)

            # Rate limiting between batches
            elif (i + self.batch_size) < len(make_series_models):
                await asyncio.sleep(self.request_delay)


        logger.info(f"Completed URL extraction: {successful_calls} successful extractions, {failed_calls} failed extractions, {total_urls} total URLs extracted")
        
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
            scripts = soup.find_all("script", type="application/ld+json")

            for script in scripts:
                if script.string:
                    data = json.loads(script.string)

                    if isinstance(data, dict):
                        if any(t in data.get("@type") for t in ["Product", "Car", "Vehicle"]):
                            return data

        except (json.JSONDecodeError, AttributeError) as e:
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
        year = json_data.get("modelDate") or json_data.get("vehicleModelDate") or json_data.get("dateVehicleFirstRegistered")
        if year:
            try:
                if isinstance(year, (int, float)):
                    data["year"] = int(year)
                else:
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

        # Mileage from description
        desc = json_data.get("description", "")
        if desc and "km" in desc.lower():
            parts = desc.split(",")
            for part in parts:
                if "km" in part.lower():
                    km_match = re.search(r"(\d[\d\s]+)\s*km", part, re.I)
                    if km_match:
                        km_str = km_match.group(1).replace("\xa0", "").replace(" ", "")
                        try:
                            data["mileage"] = float(km_str)
                            break
                        except ValueError:
                            pass

        # Fuel type
        fuel = json_data.get("fuelType") or json_data.get("fuelEfficiency")
        data["fuel_type"] = self._normalize_fuel_type(fuel)

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

        # Extract from HTML tables
        details = {}
        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                th = row.find("th")
                td = row.find("td")
                if th and td:
                    label = self._extract_text(th).lower().strip()
                    value = self._extract_text(td).strip()
                    if label and value and value != "-":
                        details[label] = value

        # Fill from details
        if not data.get("make"):
            data["make"] = details.get("mark") or details.get("make") or details.get("brand")
        if not data.get("model"):
            data["model"] = details.get("mudel") or details.get("model")

        for crumb in soup.select("div.card-body a"):
            href = crumb.get("href", "")

            if ("model_id") in href and ("year" not in href):
                data["model"] = self._extract_text(crumb)
                break
        
        year_text = details.get("aasta") or details.get("year")
        if year_text:
            year_match = re.search(r"(19|20)\d{2}", str(year_text))
            if year_match:
                data["year"] = int(year_match.group())

        # Mileage
        mileage_text = details.get("läbisõit") or details.get("km") or details.get("odomeeter") or details.get("mileage")
        if mileage_text:
            data["mileage"] = self._extract_number(mileage_text)

        if not data.get("mileage"):
            all_text = soup.get_text()
            km_patterns = [
                re.compile(r"läbisõit[:\s]+(\d[\d\s]+)\s*km", re.I),
                re.compile(r"(\d{1,3}(?:\s?\d{3})+)\s*km", re.I),
            ]
            for pattern in km_patterns:
                match = pattern.search(all_text)
                if match:
                    km_str = match.group(1).replace("\xa0", "").replace(" ", "")
                    try:
                        data["mileage"] = float(km_str)
                        break
                    except ValueError:
                        pass

        # Fuel type
        fuel = details.get("kütus") or details.get("fuel") or details.get("kütusetüüp")
        data["fuel_type"] = self._normalize_fuel_type(fuel)

        # Transmission
        data["transmission"] = details.get("käigukast") or details.get("transmission") or details.get("gearbox")

        # Body type
        data["body_type"] = details.get("keretüüp") or details.get("tüüp") or details.get("body type")

        # Color
        data["color"] = details.get("värv") or details.get("color")

        # Price fallback
        all_text = soup.get_text()
        price_pattern = re.compile(r"(\d{1,3}(?:\s?\d{3})*)\s*€")
        prices = price_pattern.findall(all_text)
        if prices:
            valid_prices = []
            for p in prices:
                p_clean = p.replace("\xa0", "").replace(" ", "")
                try:
                    p_val = float(p_clean)
                    if 100 <= p_val <= 1000000:
                        valid_prices.append(p_val)
                except ValueError:
                    pass
            if valid_prices:
                data["price"] = max(valid_prices)

        # Extract description
        desc_elem = (
            soup.find("div", class_=re.compile(r"description|desc|content")) or
            soup.find("div", id=re.compile(r"description|desc")) or
            soup.find("section", class_=re.compile(r"description|desc|content"))
        )
        if desc_elem:
            # Check if it's navigation content
            parent = desc_elem.parent
            is_nav = False
            for _ in range(5):
                if parent:
                    parent_classes = " ".join(parent.get("class", [])).lower()
                    parent_id = parent.get("id", "").lower()
                    if any(x in parent_classes + parent_id for x in ["nav", "header", "menu", "sidebar"]):
                        is_nav = True
                        break
                    parent = parent.parent

            if not is_nav:
                description = self._extract_text(desc_elem)
                # Filter out navigation text
                nav_patterns = [
                    "logi sisse", "registreeri", "kuulutused", "varuosad",
                    "süsteemiseaded", "hele teema", "tume teema", "sündmused",
                    "partnerid", "rent", "uudised"
                ]
                desc_lower = description.lower().replace(" ", "") if description else ""
                if description and not any(p.replace(" ", "") in desc_lower for p in nav_patterns):
                    if len(description) >= 100 or any(c in description for c in ".!?,;"):
                        data["description"] = description[:2000] if len(description) > 2000 else description

        # Extract image
        for img in soup.find_all("img"):
            src = img.get("src", "") or img.get("data-src", "") or img.get("data-lazy-src", "") or img.get("data-original", "")
            if src and "api.veego.ee" in src and "vehicles/imgs" in src:
                if not any(skip in src.lower() for skip in ["logo", "icon", "thumb", "flag", "placeholder", "empty", "button", "svg"]):
                    data["image_url"] = src
                    break

        return data

    def _normalize_fuel_type(self, fuel_type: Optional[str]) -> Optional[str]:
        """Normalize fuel type to standard values."""
        if not fuel_type:
            return None

        fuel_lower = fuel_type.lower().strip()

        if "hybrid" in fuel_lower or "hübriid" in fuel_lower:
            return "Hübriid"
        elif "bensiin" in fuel_lower or "petrol" in fuel_lower or "gasoline" in fuel_lower:
            return "Bensiin"
        elif "diisel" in fuel_lower or "diesel" in fuel_lower:
            return "Diisel"
        elif "elekter" in fuel_lower or "electric" in fuel_lower:
            return "Elekter"
        else:
            return fuel_lower.capitalize() if fuel_lower else None

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
        Parse a single veego listing.

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
                "series": None,
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
            logger.error(f"Error parsing Veego listing {url}: {e}")
            return None
        
    async def _fetch_and_parse_listing(self, url: str, make_series_model: tuple[str, str | None, str]) -> Optional[Dict]:
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
                listing_data["source_taxonomy"] = {
                    "make_id": make_series_model[0],
                    "series_id": make_series_model[1],
                    "model_id": make_series_model[2],
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
        
        tasks = [self._fetch_and_parse_listing(url, make_series_model) for url, make_series_model in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        listings = []
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                logger.error(f"Exception for {url}: {result}")
            elif result is not None:
                listings.append(result)
        
        return listings
        
    async def scrape_all(self, max_pages: Optional[int] = None) -> List[Dict]:
        page = await self.fetch_page("https://veego.ee/_nuxt/D7p4OLQY.js")
        self.translator = VeegoTranslator.from_js_string(page)

        # Get all makes and models for translation lookup
        make_ids = await self._get_makes()

        async def fetch_models_for_make(make_id: str):
            await self._get_models(make_id)

        await asyncio.gather(*(fetch_models_for_make(mid) for mid in make_ids))
        self.unique_sub_models = list(set(self.models_lookup.values()))
        logger.info(f"Starting scrape of Veego.ee with max_pages={max_pages}")
        urls = await self.get_listing_urls(max_pages)
        logger.info(f"Found {len(urls)} listings to scrape from {self.site_name}")

        if not urls:
            return []

        # Split URLs into batches
        batches = [urls[i : i + self.batch_size] for i in range(0, len(urls), self.batch_size)]
        total_batches = len(batches)
        
        all_listings = []
        
        for batch_num, batch_urls in enumerate(batches, 1):
            batch_listings = await self._process_batch(batch_urls, batch_num, total_batches)
            all_listings.extend(batch_listings)
            
            # Rate limiting between batches
            if batch_num < total_batches:
                await asyncio.sleep(self.request_delay)

        logger.info(f"Successfully scraped {len(all_listings)} listings from {self.site_name}")
        return all_listings