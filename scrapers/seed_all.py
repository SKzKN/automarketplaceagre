
import logging
import sys
import time

from curl_cffi.requests import Session

from .config import get_config
from .repository import ScraperRepository
from .mark_top_brands import main as mark_top_brands
from .seeders.seed_auto24_catalog import Auto24TaxonomyExtractor
from .seeders.seed_autodiiler import AutodiilerExtractor
from .seeders.seed_veego import VeegoExtractor, VeegoTranslator
from .seeders.seed_source_taxonomy import seed_source_taxonomy


logger = logging.getLogger(__name__)


def run_all_seeders() -> None:
    """Run all taxonomy seeders and mark top brands."""
    config = get_config()

    logging.basicConfig(
        level=getattr(logging, config.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    repo = ScraperRepository(config)
    repo.connect()

    session = Session(impersonate="chrome")

    total_start = time.time()

    try:
        # 1) Seed Auto24 canonical taxonomy (primary source)
        logger.info("=" * 60)
        logger.info("STEP 1/4: Seeding Auto24 taxonomy (canonical base)...")
        logger.info("=" * 60)
        try:
            auto24_extractor = Auto24TaxonomyExtractor(session)
            auto24_counts = seed_source_taxonomy(repo, auto24_extractor)
            logger.info("Auto24 seeding complete: %s", auto24_counts)
        except Exception as e:
            logger.error("Auto24 seeding failed: %s", e)

        # 2) Seed AutoDiiler taxonomy mappings
        logger.info("=" * 60)
        logger.info("STEP 2/4: Seeding AutoDiiler taxonomy mappings...")
        logger.info("=" * 60)
        try:
            autodiiler_extractor = AutodiilerExtractor(session=session)
            autodiiler_counts = seed_source_taxonomy(repo, autodiiler_extractor)
            logger.info("AutoDiiler seeding complete: %s", autodiiler_counts)
        except Exception as e:
            logger.error("AutoDiiler seeding failed: %s", e)

        # 3) Seed Veego taxonomy mappings
        logger.info("=" * 60)
        logger.info("STEP 3/4: Seeding Veego taxonomy mappings...")
        logger.info("=" * 60)
        try:
            page = session.get("https://veego.ee/_nuxt/D7p4OLQY.js")
            translator = VeegoTranslator.from_js_string(js_string=page.text)
            veego_extractor = VeegoExtractor(session=session, translator=translator)
            veego_counts = seed_source_taxonomy(repo, veego_extractor)
            logger.info("Veego seeding complete: %s", veego_counts)
        except Exception as e:
            logger.error("Veego seeding failed: %s", e)

        # 4) Mark top brands
        logger.info("=" * 60)
        logger.info("STEP 4/4: Marking top brands...")
        logger.info("=" * 60)
        try:
            mark_top_brands()
        except Exception as e:
            logger.error("Mark top brands failed: %s", e)

        elapsed = time.time() - total_start
        logger.info("=" * 60)
        logger.info("ALL SEEDING COMPLETE (%.1fs)", elapsed)
        logger.info("=" * 60)

    finally:
        repo.disconnect()
        session.close()


if __name__ == "__main__":
    run_all_seeders()
