import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from bson import ObjectId
from pymongo import MongoClient, UpdateOne
from pymongo.collection import Collection, ReturnDocument
from pymongo.database import Database

from .config import ScraperConfig, get_config

logger = logging.getLogger(__name__)

# Normalization expressions for human-friendly labels (ET) - used for both canonical catalog and source labels.
_RE_MULTI_SPACE = re.compile(r"\s+")
_RE_NUM_DOT = re.compile(r"(\d)\.")  # "2. seeria" -> "2 seeria"


def clean_label(label: str) -> str:
    """Human-friendly label (ET) for storage/display."""
    s = (label or "").strip()

    # auto24 UI suffix "(kõik)" = "all" (noise for our catalog)
    if s.lower().endswith("(kõik)"):
        s = s[: -len("(kõik)")].strip()

    # unify "2. seeria" -> "2 seeria"
    s = _RE_NUM_DOT.sub(r"\1", s)

    # collapse spaces
    s = _RE_MULTI_SPACE.sub(" ", s)
    return s


def norm_label(label: str) -> str:
    """Deterministic key used for matching + uniqueness."""
    return clean_label(label).lower()


def utcnow() -> datetime:
    return datetime.utcnow()


class ScraperRepository:
    """
    Scraper-side MongoDB repository.

    Collections (no catalog_ prefix):
    - car_listings (config.collection_name)
    - makes
    - series
    - models
    - taxonomy_mappings
    """

    MAKES_COL = "makes"
    SERIES_COL = "series"
    MODELS_COL = "models"
    MAPPINGS_COL = "taxonomy_mappings"

    def __init__(self, config: Optional[ScraperConfig] = None):
        self.config = config or get_config()
        self._client: Optional[MongoClient] = None
        self._db: Optional[Database] = None

    # -------- Connection / collections
    def connect(self) -> None:
        if self._client is not None:
            return

        self._client = MongoClient(self.config.mongodb_uri)
        self._db = self._client.get_database(self.config.database_name)
        self._ensure_indexes()
        logger.info("Connected to MongoDB: %s", self.config.database_name)

    def disconnect(self) -> None:
        if self._client:
            self._client.close()
        self._client = None
        self._db = None
        logger.info("Disconnected from MongoDB")

    @property
    def db(self) -> Database:
        if self._db is None:
            self.connect()
        return self._db  # type: ignore

    def col(self, name: str) -> Collection:
        return self.db[name]

    @property
    def car_listings(self) -> Collection:
        return self.col(self.config.collection_name)

    @property
    def makes(self) -> Collection:
        return self.col(self.MAKES_COL)

    @property
    def series(self) -> Collection:
        return self.col(self.SERIES_COL)

    @property
    def models(self) -> Collection:
        return self.col(self.MODELS_COL)

    @property
    def mappings(self) -> Collection:
        return self.col(self.MAPPINGS_COL)

    def _ensure_indexes(self) -> None:
        """
        Create indexes for better query performance.
        In MongoDB this also effectively 'creates' collections.
        """

        # 1) listings
        listings = self.car_listings
        listings.create_index("source_url", unique=True)
        listings.create_index("source_site")
        listings.create_index("make")
        listings.create_index("series")
        listings.create_index("model")
        listings.create_index("price")
        listings.create_index("year")

        # last_seen bookkeeping (for stale deletion)
        listings.create_index([("source_site", 1), ("last_seen_run_id", 1)])
        listings.create_index([("source_site", 1), ("last_seen_at", 1)])

        # future-proof: canonical ids (resolver will set them later)
        listings.create_index("make_id")
        listings.create_index("series_id")
        listings.create_index("model_id")
        listings.create_index([("make_id", 1), ("series_id", 1), ("model_id", 1)])

        # 2) makes
        makes = self.makes
        makes.create_index("norm", unique=True)
        makes.create_index("name_et")

        # 3) series
        series = self.series
        series.create_index([("make_id", 1), ("norm", 1)], unique=True)
        series.create_index([("make_id", 1), ("name_et", 1)])

        # 4) models
        models = self.models
        models.create_index([("make_id", 1), ("series_id", 1), ("norm", 1)], unique=True)
        models.create_index([("make_id", 1), ("series_id", 1)])
        models.create_index([("make_id", 1), ("name_et", 1)])

        # 5) mappings
        mappings = self.mappings
        # Main path for text-based resolution (auto24 listing pages have no ids)
        mappings.create_index(
            [
                ("source_site", 1),
                ("entity_type", 1),
                ("make_canonical_id", 1),
                ("series_canonical_id", 1),
                ("source_norm", 1),
            ],
            unique=True,
        )
        # Additional path for sources with stable numeric ids (veego/autodiiler APIs)
        mappings.create_index(
            [
                ("source_site", 1),
                ("entity_type", 1),
                ("make_canonical_id", 1),
                ("source_key", 1),
            ]
        )

    def delete_stale_listings(self, *, source_site: str, run_id: str) -> int:
        """
        Delete listings that were NOT seen in the current run for a specific source_site.
        Use only after a successful scrape of that source_site.
        """
        res = self.car_listings.delete_many(
            {
                "source_site": source_site,
                "last_seen_run_id": {"$ne": run_id},
            }
        )
        return int(res.deleted_count or 0)

    def save_listing(self, listing_data: Dict[str, Any], *, run_id: Optional[str] = None) -> bool:
        """
        Upsert a single listing by source_url.

        If run_id is provided, sets last_seen_run_id/last_seen_at for stale deletion.

        Returns:
            True  -> inserted new
            False -> matched existing (updated or already same)
        """
        if not listing_data.get("source_url"):
            raise ValueError("listing_data must contain 'source_url'")
        if not listing_data.get("source_site"):
            raise ValueError("listing_data must contain 'source_site'")

        now = utcnow()
        update_set = {k: v for k, v in listing_data.items() if k != "_id"}
        update_set["updated_at"] = now

        if run_id is not None:
            update_set["last_seen_run_id"] = run_id
            update_set["last_seen_at"] = now

        res = self.car_listings.update_one(
            {"source_url": listing_data["source_url"]},
            {"$set": update_set, "$setOnInsert": {"created_at": now}},
            upsert=True,
        )
        return res.upserted_id is not None

    def save_listings(
        self,
        listings: List[Dict[str, Any]],
        *,
        run_id: Optional[str] = None,
    ) -> Dict[str, int]:
        """
        Bulk upsert listings.

        If run_id is provided, sets last_seen_run_id/last_seen_at for each saved doc.

        Note:
        - We do NOT do cleanup here automatically because caller controls per-source flow.
        - If you want cleanup, call delete_stale_listings(source_site, run_id) after scrape.

        Returns:
            dict(saved, updated, errors, processed)
        """
        if not listings:
            return {"saved": 0, "updated": 0, "errors": 0, "processed": 0}

        now = utcnow()
        ops: List[UpdateOne] = []
        errors = 0
        processed = 0

        for item in listings:
            try:
                source_url = item.get("source_url")
                source_site = item.get("source_site")
                if not source_url:
                    raise ValueError("missing source_url")
                if not source_site:
                    raise ValueError("missing source_site")

                update_set = {k: v for k, v in item.items() if k != "_id"}
                update_set["updated_at"] = now

                if run_id is not None:
                    update_set["last_seen_run_id"] = run_id
                    update_set["last_seen_at"] = now

                ops.append(
                    UpdateOne(
                        {"source_url": source_url},
                        {"$set": update_set, "$setOnInsert": {"created_at": now}},
                        upsert=True,
                    )
                )
                processed += 1
            except Exception as e:
                errors += 1
                logger.error("Invalid listing payload (%s): %s", item.get("source_url"), e)

        if not ops:
            return {"saved": 0, "updated": 0, "errors": errors, "processed": processed}

        result = self.car_listings.bulk_write(ops, ordered=False)
        saved = int(getattr(result, "upserted_count", 0) or 0)
        updated = int(getattr(result, "matched_count", 0) or 0)

        logger.info("Listings bulk upsert: saved=%s updated=%s errors=%s processed=%s", saved, updated, errors, processed)
        return {"saved": saved, "updated": updated, "errors": errors, "processed": processed}

    def upsert_make(self, name_et: str) -> ObjectId:
        """Upsert canonical make by normalized name."""
        name = clean_label(name_et)
        norm = norm_label(name)
        now = utcnow()

        doc = self.makes.find_one_and_update(
            {"norm": norm},
            {"$set": {"name_et": name, "updated_at": now}, "$setOnInsert": {"created_at": now}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return doc["_id"]

    def upsert_series(self, make_id: ObjectId, name_et: str) -> ObjectId:
        """Upsert canonical series under make."""
        name = clean_label(name_et)
        norm = norm_label(name)
        now = utcnow()

        doc = self.series.find_one_and_update(
            {"make_id": make_id, "norm": norm},
            {
                "$set": {"name_et": name, "updated_at": now},
                "$setOnInsert": {"created_at": now, "make_id": make_id},
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return doc["_id"]

    def upsert_model(self, make_id: ObjectId, name_et: str, series_id: Optional[ObjectId] = None) -> ObjectId:
        """Upsert canonical model under make (+ optional series)."""
        name = clean_label(name_et)
        norm = norm_label(name)
        now = utcnow()

        doc = self.models.find_one_and_update(
            {"make_id": make_id, "series_id": series_id, "norm": norm},
            {
                "$set": {"name_et": name, "updated_at": now},
                "$setOnInsert": {"created_at": now, "make_id": make_id, "series_id": series_id},
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return doc["_id"]

    def upsert_mapping(
        self,
        *,
        source_site: str,
        entity_type: str,  # "make" | "series" | "model"
        source_label: str,
        canonical_id: ObjectId,
        make_canonical_id: Optional[ObjectId] = None,
        series_canonical_id: Optional[ObjectId] = None,
        source_key: Optional[str] = None,
        method: str = "auto",
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Upsert source -> canonical mapping.

        auto24 listing pages have no ids => we must be able to resolve by source_label (source_norm).
        veego/autodiiler APIs have ids => we also store source_key for exact matching.
        """
        now = utcnow()
        label = clean_label(source_label)
        src_norm = norm_label(label)

        filt = {
            "source_site": source_site,
            "entity_type": entity_type,
            "make_canonical_id": make_canonical_id,
            "series_canonical_id": series_canonical_id,
            "source_norm": src_norm,
        }

        set_part: Dict[str, Any] = {
            "source_label": label,
            "source_norm": src_norm,
            "canonical_id": canonical_id,
            "source_key": source_key,
            "method": method,
            "updated_at": now,
        }
        if extra:
            set_part.update({f"extra.{k}": v for k, v in extra.items()})

        self.mappings.update_one(
            filt,
            {
                "$set": set_part,
                "$setOnInsert": {
                    "created_at": now,
                    "source_site": source_site,
                    "entity_type": entity_type,
                    "make_canonical_id": make_canonical_id,
                    "series_canonical_id": series_canonical_id,
                },
            },
            upsert=True,
        )

    def find_make_id(self, make_name: str) -> Optional[ObjectId]:
        doc = self.makes.find_one({"norm": norm_label(make_name)}, {"_id": 1})
        return doc["_id"] if doc else None

    def find_series_id(self, make_id: ObjectId, series_name: str) -> Optional[ObjectId]:
        doc = self.series.find_one({"make_id": make_id, "norm": norm_label(series_name)}, {"_id": 1})
        return doc["_id"] if doc else None

    def find_model_id(self, make_id: ObjectId, model_name: str, series_id: Optional[ObjectId] = None) -> Optional[ObjectId]:
        doc = self.models.find_one({"make_id": make_id, "series_id": series_id, "norm": norm_label(model_name)}, {"_id": 1})
        return doc["_id"] if doc else None

    def get_listing_count(self) -> int:
        return int(self.car_listings.count_documents({}))

    def get_listing_count_by_source(self, source_site: str) -> int:
        return int(self.car_listings.count_documents({"source_site": source_site}))
