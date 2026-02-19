import asyncio
import logging
import sys
import time
import uuid
from typing import Dict, List, Type, Union

from .config import get_config, ScraperConfig
from .repository import ScraperRepository
from .resolver import resolve_all_unresolved
from .scrapers import (
    BaseScraper,
    AsyncBaseScraper,
    Auto24Scraper,
    AutoDiilerScraper,
    AutoportaalScraper,
    VeegoScraper,
    OkidokiScraper,
)

def setup_logging(log_level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("scrapers.log"),
        ],
    )


def get_active_scrapers() -> List[Type[Union[BaseScraper, AsyncBaseScraper]]]:
    return [
        AutoDiilerScraper,   # ✅ Async with JSON-LD + HTML fallback
        Auto24Scraper,       # ✅ Async with curl_cffi (Cloudflare bypass)
        VeegoScraper,        # ✅ Async with public API + JSON-LD
        # OkidokiScraper,    # ❌ Cloudflare protection (403)
        #AutoportaalScraper,  # ✅ Async with JSON-LD + HTML fallback
    ]


async def run_single_scraper(
    scraper_class: Type[Union[BaseScraper, AsyncBaseScraper]],
    config: ScraperConfig,
    repository: ScraperRepository,
    logger: logging.Logger,
    run_id: str,
) -> Dict[str, int]:
    scraper = scraper_class(
        batch_size=config.batch_size,
        request_delay=config.request_delay,
        request_timeout=config.request_timeout,
    )
    site_name = scraper.site_name
    
    try:
        logger.info(f"Starting scraper for {site_name}...")
        start_time = time.time()
        
        async with scraper:
            listings = await scraper.scrape_all(max_pages=config.max_pages)

        elapsed = time.time() - start_time
        
        if listings:
            result = repository.save_listings(listings, run_id=run_id)

            # Delete listings that disappeared from the source.
            # Important: we only do cleanup when we successfully scraped SOME listings.
            deleted = repository.delete_stale_listings(source_site=site_name, run_id=run_id)
            logger.info(
                f"{site_name}: {result['saved']} new, "
                f"{result['updated']} updated, {result['errors']} errors "
                f"(deleted {deleted} stale, took {elapsed:.1f}s)"
            )
            return {"site": site_name, **result, "deleted": deleted, "elapsed": elapsed}
        else:
            logger.warning(f"{site_name}: No listings scraped (took {elapsed:.1f}s)")
            # Safety: if we scraped 0 listings, DO NOT delete anything.
            return {"site": site_name, "saved": 0, "updated": 0, "errors": 0, "deleted": 0, "elapsed": elapsed}
            
    except Exception as e:
        logger.error(f"Error running {site_name} scraper: {e}")
        return {"site": site_name, "saved": 0, "updated": 0, "errors": 0, "error": str(e)}


async def run_all_scrapers_async(
    scraper_classes: List[Type[Union[BaseScraper, AsyncBaseScraper]]],
    config: ScraperConfig,
    repository: ScraperRepository,
    logger: logging.Logger,
    run_id: str,
) -> List[Dict]:
    logger.info(f"Running {len(scraper_classes)} scrapers concurrently...")
    
    tasks = [
        run_single_scraper(scraper_class, config, repository, logger, run_id)
        for scraper_class in scraper_classes
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle any exceptions that were returned
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            site_name = scraper_classes[i].__name__
            logger.error(f"Exception in {site_name}: {result}")
            processed_results.append({"site": site_name, "error": str(result)})
        else:
            processed_results.append(result)
    
    return processed_results


def main():
    config = get_config()
    setup_logging(config.log_level)

    logger = logging.getLogger(__name__)
    run_id = uuid.uuid4().hex
    logger.info("Starting scraper run (run_id=%s)...", run_id)

    repository = ScraperRepository(config)

    try:
        repository.connect()

        scraper_classes = get_active_scrapers()
        
        start_time = time.time()
        
        # Run all scrapers concurrently
        results = asyncio.run(
            run_all_scrapers_async(scraper_classes, config, repository, logger, run_id)
        )
        
        total_elapsed = time.time() - start_time
        resolve_all_unresolved(repository, limit=0)  # Resolve canonical IDs for all listings after scraping
        # Summary
        total_saved = sum(r.get("saved", 0) for r in results)
        total_updated = sum(r.get("updated", 0) for r in results)
        total_errors = sum(r.get("errors", 0) for r in results)
        total_deleted = sum(r.get("deleted", 0) for r in results)
        
        logger.info("=" * 50)
        logger.info("SCRAPING SUMMARY")
        logger.info("=" * 50)
        for result in results:
            site = result.get("site", "unknown")
            if "error" in result and "saved" not in result:
                logger.info(f"  {site}: FAILED - {result['error']}")
            else:
                elapsed = result.get("elapsed", 0)
                logger.info(
                    f"  {site}: {result.get('saved', 0)} new, "
                    f"{result.get('updated', 0)} updated, "
                    f"{result.get('errors', 0)} errors, "
                    f"{result.get('deleted', 0)} deleted ({elapsed:.1f}s)"
                )
        logger.info("-" * 50)
        logger.info(
            f"TOTAL: {total_saved} new, {total_updated} updated, "
            f"{total_deleted} deleted, {total_errors} errors"
        )
        logger.info(f"Total time: {total_elapsed:.1f}s (concurrent)")
        
        total_listings = repository.get_listing_count()
        logger.info(f"Total listings in database: {total_listings}")

    finally:
        repository.disconnect()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt: 
        print("Scraper run interrupted by user")