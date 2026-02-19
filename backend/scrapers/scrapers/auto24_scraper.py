import asyncio
import logging
import re
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from .curl_cffi_scraper import CurlCffiScraper
from curl_cffi.requests.exceptions import HTTPError, Timeout

logger = logging.getLogger(__name__)


class Auto24Scraper(CurlCffiScraper):
    """
    Async scraper for Auto24.ee with Cloudflare bypass.

    Inherits from CurlCffiScraper which uses curl_cffi with browser impersonation
    to bypass Cloudflare protection.
    """

    def __init__(
        self,
        batch_size: int = 5,
        request_delay: float = 1.0,
        request_timeout: int = 30,
    ):
        """
        Initialize Auto24 scraper.

        Args:
            batch_size: Number of listings to fetch concurrently
            request_delay: Delay between batches in seconds
            request_timeout: Timeout for individual requests
        """
        super().__init__(
            base_url="https://www.auto24.ee",
            site_name="auto24",
            batch_size=batch_size,
            request_delay=request_delay,
            request_timeout=request_timeout,
            impersonate="chrome",
            max_retries=3,
        )

    async def get_listing_urls(self, max_pages: Optional[int] = 10) -> List[str]:
        """Get URLs of all car listing pages."""
        logger.info(f"Starting to fetch listing URLs from Auto24 (max_pages={max_pages})")
        urls = set()

        if max_pages is None:
            # Unlimited - keep fetching until no more listings
            page = 1
            while True:
                try:
                    search_url = f"{self.base_url}/kasutatud/nimekiri.php"
                    if page > 1:
                        search_url = f"{search_url}?ak={(page - 1) * 50}"

                    soup = await self.fetch_page_soup(search_url)
                    if not soup:
                        logger.warning(f"Could not fetch page {page}")
                        break

                    current_page = soup.select_one("span.page-cntr")
                    if (
                        not current_page
                        or int(current_page.text.split("/")[0].replace("(", "").strip())
                        < page
                    ):
                        logger.info(f"No more pages after page {page - 1}")
                        break

                    page_urls = self._extract_listing_urls_from_page(soup)
                    if not page_urls:
                        logger.info(f"No more listings on page {page}")
                        break

                    urls.update(page_urls)
                    logger.info(f"Page {page}: found {len(page_urls)} listings")
                    page += 1
                    await asyncio.sleep(self.request_delay)  # Small delay between pages
                except HTTPError as e:
                    logger.error(f"HTTP error fetching page {page}: {e}")
                    break
                except Timeout:
                    logger.error(f"Timeout fetching page {page}")
                    break
                except Exception as e:
                    logger.error(f"Error fetching page {page}: {e}")
                    break
        else:
            # Limited pages
            for page in range(1, max_pages + 1):
                try:
                    search_url = f"{self.base_url}/kasutatud/nimekiri.php"
                    if page > 1:
                        search_url = f"{search_url}?ak={(page - 1) * 50}"

                    soup = await self.fetch_page_soup(search_url)
                    if not soup:
                        logger.warning(f"Could not fetch page {page}")
                        break

                    current_page = soup.select_one("span.page-cntr")
                    if (
                        not current_page
                        or int(current_page.text.split("/")[0].replace("(", "").strip())
                        < page
                    ):
                        logger.info(f"No more pages after page {page - 1}")
                        break

                    page_urls = self._extract_listing_urls_from_page(soup)
                    if not page_urls:
                        logger.info(f"No more listings on page {page}")
                        break

                    urls.update(page_urls)
                    logger.info(f"Page {page}: found {len(page_urls)} listings")
                    await asyncio.sleep(self.request_delay)
                except HTTPError as e:
                    logger.error(f"HTTP error fetching page {page}: {e}")
                    break
                except Timeout:
                    logger.error(f"Timeout fetching page {page}")
                    break
                except Exception as e:
                    logger.error(f"Error fetching page {page}: {e}")
                    break

        urls_list = list(urls)
        logger.info(f"Total listing URLs found: {len(urls_list)}")
        return urls_list

    def _extract_listing_urls_from_page(self, soup: BeautifulSoup) -> List[str]:
        """Extract listing URLs from a search results page."""
        urls = []

        # Find listing links
        listing_links = soup.select("a.row-link")

        for link in listing_links:
            href = link.get("href")
            if href:
                if href.startswith("/"):
                    full_url = self.base_url + href
                else:
                    full_url = href

                # Normalize to Estonian URL format
                if "/vehicles/" in full_url:
                    id_match = re.search(r"/vehicles/(\d+)", full_url)
                    if id_match:
                        full_url = f"{self.base_url}/soidukid/{id_match.group(1)}"

                if full_url not in urls:
                    urls.append(full_url)

        return urls

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
        title_elem = soup.find("h1") or soup.find("title")
        data["title"] = self._extract_text(title_elem)

        breadcrumbs = soup.select(".b-breadcrumbs a.b-breadcrumbs__item")

        for crumb in breadcrumbs:
            crumb_href = crumb.get("href", "")

            if not ("f1" in crumb_href or "f2" in crumb_href):
                if crumb_href.count("bw") == 2:
                    data["model"] = self._extract_text(crumb)
                elif crumb_href.count("bw") == 1:
                    data["series"] = self._extract_text(crumb)
                elif crumb_href.count("bw") == 0 and crumb_href.count("b=") == 1:
                    data["make"] = self._extract_text(crumb)

        # Extract price
        data["price"] = self._extract_price(soup)

        # Extract details from data-container
        details = self._extract_details(soup)

        if not data.get("year"):
            year_text = (
                details.get("esmane reg")
                or details.get("aasta")
                or details.get("esmane registreerimine")
            )
            if year_text:
                year_match = re.search(r"\b(19|20)\d{2}\b", str(year_text))
                if year_match:
                    data["year"] = int(year_match.group())

        # Mileage
        data["mileage"] = self._extract_mileage(soup, details)

        # Fuel type
        data["fuel_type"] = self._normalize_fuel_type(
            details.get("kütus") or details.get("kütusetüüp")
        )

        # Transmission
        data["transmission"] = details.get("käigukast")

        # Body type
        data["body_type"] = details.get("keretüüp")

        # Color
        data["color"] = details.get("värvus") or details.get("värv")

        # Description
        data["description"] = self._extract_description(soup)

        # Image
        data["image_url"] = self._extract_image(soup)

        return data

    def _extract_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract price from page."""
        price = None

        # Method 1: data-container structure
        data_container = soup.find("div", class_="data-container")
        if data_container:
            text = data_container.get_text(separator="\n", strip=True)
            lines = [line.strip() for line in text.split("\n") if line.strip()]

            # Look for "Soodushind" (sale price) or "Hind" (price)
            for i, line in enumerate(lines):
                if line.lower() in ["soodushind", "hind"] and i + 1 < len(lines):
                    price_text = lines[i + 1]
                    price_match = re.search(r"(\d[\d\s\xa0]+)", price_text)
                    if price_match:
                        try:
                            price_str = (
                                price_match.group(1)
                                .replace(" ", "")
                                .replace("\xa0", "")
                            )
                            price = float(price_str)
                            if (
                                line.lower() == "soodushind"
                            ):  # Sale price takes priority
                                break
                        except ValueError:
                            pass

        # Method 2: Regex fallback
        if not price:
            all_text = soup.get_text()
            price_pattern = re.compile(r"(\d{1,3}(?:\s?\d{3})*)\s*€")
            prices = price_pattern.findall(all_text)
            if prices:
                valid_prices = []
                for p in prices:
                    p_clean = p.replace(" ", "")
                    try:
                        p_val = float(p_clean)
                        if 100 <= p_val <= 500000:
                            valid_prices.append(p_val)
                    except ValueError:
                        pass
                if valid_prices:
                    valid_prices.sort()
                    price = (
                        valid_prices[len(valid_prices) // 2]
                        if len(valid_prices) > 2
                        else valid_prices[-1]
                    )

        return price

    def _extract_details(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract details from page structure."""
        details = {}

        # Method 1: data-container section
        data_container = soup.find("div", class_="data-container")
        if data_container:
            text = data_container.get_text(separator="\n", strip=True)
            lines = [line.strip() for line in text.split("\n") if line.strip()]

            i = 0
            while i < len(lines) - 1:
                key = lines[i].lower()
                value = lines[i + 1]
                if key and value and value.lower() != key:
                    details[key] = value
                    i += 2
                else:
                    i += 1

        # Method 2: Table rows
        for row in soup.find_all("tr"):
            th = row.find("th")
            td = row.find("td")
            if th and td:
                label = self._extract_text(th).lower()
                value = self._extract_text(td)
                if label and value and label not in details:
                    details[label] = value

        return details

    def _extract_mileage(self, soup: BeautifulSoup, details: Dict) -> Optional[float]:
        """Extract mileage from page."""
        mileage_text = (
            details.get("läbisõidumõõdiku näit")
            or details.get("läbisõit")
            or details.get("odomeeter")
            or details.get("odomeetri näit")
        )
        if mileage_text:
            return self._extract_number(mileage_text)

        # Fallback: regex on page text
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
                    return float(km_str)
                except ValueError:
                    pass

        return None

    def _normalize_fuel_type(self, fuel_type: Optional[str]) -> Optional[str]:
        """Normalize fuel type to standard values."""
        if not fuel_type:
            return None

        fuel_lower = fuel_type.lower().strip()

        if "hybrid" in fuel_lower or "hübriid" in fuel_lower:
            return "Hübriid"
        elif "bensiin" in fuel_lower or "petrol" in fuel_lower:
            return "Bensiin"
        elif "diisel" in fuel_lower or "diesel" in fuel_lower:
            return "Diisel"
        elif "elekter" in fuel_lower or "electric" in fuel_lower:
            return "Elekter"
        else:
            return fuel_lower.capitalize() if fuel_lower else None

    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract description from page."""
        other_info = soup.find(
            "div", class_=re.compile(r"other-info|other_info|lisainfo")
        )
        if other_info:
            desc_text = other_info.get_text(separator=" ", strip=True)
            # Clean up common noise
            desc_text = re.sub(r"Eestis arvel[^.]*\.", "", desc_text)
            desc_text = re.sub(r"Sõiduki asukoht:[^.]*\.", "", desc_text)
            desc_text = re.sub(r"Müüja[^.]*\.", "", desc_text)
            desc_text = re.sub(r"Salvesta|Jaga|Võrdle|Prindi|Teavita", "", desc_text)
            desc_text = desc_text.strip()
            if desc_text and len(desc_text) > 20:
                return desc_text[:2000]

        return None

    def _extract_image(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract main image URL."""
        main_image = soup.select_one("div#lightgallery img")

        if main_image and main_image.has_attr("src"):
            return main_image["src"]
        return None

    def parse_listing(self, url: str, html: str) -> Optional[Dict]:
        """
        Parse a single Auto24 listing from HTML content.

        Args:
            url: URL of the listing
            html: HTML content of the page

        Returns:
            Dictionary with car listing data or None if parsing failed
        """
        try:
            soup = BeautifulSoup(html, "lxml")
            result = self._parse_from_html(soup)

            return {
                "title": result.get("title"),
                "make": result.get("make"),
                "model": result.get("model"),
                "series": result.get("series"),
                "year": result.get("year"),
                "price": result.get("price"),
                "mileage": result.get("mileage"),
                "fuel_type": result.get("fuel_type"),
                "transmission": result.get("transmission"),
                "body_type": result.get("body_type"),
                "color": result.get("color"),
                "description": result.get("description"),
                "image_url": result.get("image_url"),
                "source_taxonomy" : {
                    "make_id": None,
                    "model_id": None,
                    "series_id": None
                }
            }

        except Exception as e:
            logger.error(f"Error parsing Auto24 listing {url}: {e}")
            return None
