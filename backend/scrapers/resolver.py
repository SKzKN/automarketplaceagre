from typing import Any, Dict, Optional

from bson import ObjectId

from scrapers.repository import ScraperRepository, norm_label


def _find_mapping_by_text(
    repo: ScraperRepository,
    source_site: str,
    entity_type: str,
    source_label: str,
    make_canonical_id: Optional[ObjectId],
    series_canonical_id: Optional[ObjectId],
) -> Optional[Dict[str, Any]]:
    return repo.mappings.find_one(
        {
            "source_site": source_site,
            "entity_type": entity_type,
            "make_canonical_id": make_canonical_id,
            "series_canonical_id": series_canonical_id,
            "source_norm": norm_label(source_label),
        }
    )


def _find_mapping_by_key(
    repo: ScraperRepository,
    source_site: str,
    entity_type: str,
    source_key: str,
    make_canonical_id: Optional[ObjectId],
) -> Optional[Dict[str, Any]]:
    # For series/model in id-based sources we still anchor by canonical make_id
    return repo.mappings.find_one(
        {
            "source_site": source_site,
            "entity_type": entity_type,
            "make_canonical_id": make_canonical_id,
            "source_key": str(source_key),
        }
    )


def resolve_one_listing(repo: ScraperRepository, listing: Dict[str, Any]) -> Dict[str, Optional[ObjectId]]:
    source_site = listing.get("source_site")
    make = listing.get("make")
    series = listing.get("series")
    model = listing.get("model")

    if not source_site or not make or not model:
        return {"make_id": None, "series_id": None, "model_id": None}

    source_tax = listing.get("source_taxonomy") or {}
    src_make_id = source_tax.get("make_id")
    src_series_id = source_tax.get("series_id")
    src_model_id = source_tax.get("model_id")


    # 1) make_id (canonical)
    make_map = None
    if src_make_id is not None:
        make_map = _find_mapping_by_key(
            repo, source_site=source_site, entity_type="make", source_key=str(src_make_id), make_canonical_id=None
        )
    if make_map is None:
        make_map = _find_mapping_by_text(
            repo, source_site=source_site, entity_type="make", source_label=make, make_canonical_id=None, series_canonical_id=None
        )
    make_id = make_map["canonical_id"] if make_map else None
            
    # 2) series_id (canonical)
    series_id = None
    if make_id and (series or src_series_id is not None):
        series_map = None
        if src_series_id is not None:
            series_map = _find_mapping_by_key(
                repo, source_site=source_site, entity_type="series", source_key=str(src_series_id), make_canonical_id=make_id
            )
        if series_map is None and series:
            series_map = _find_mapping_by_text(
                repo,
                source_site=source_site,
                entity_type="series",
                source_label=series,
                make_canonical_id=make_id,
                series_canonical_id=None,
            )
        if series_map:
            series_id = series_map["canonical_id"]

    # 3) model_id (canonical)
    model_id = None
    if make_id:
        model_map = None
        if src_model_id is not None:
            model_map = _find_mapping_by_key(
                repo, 
                source_site=source_site, 
                entity_type="model", 
                source_key=str(src_model_id), 
                make_canonical_id=make_id
            )
        if model_map is None:
            model_map = _find_mapping_by_text(
                repo,
                source_site=source_site,
                entity_type="model",
                source_label=model,
                make_canonical_id=make_id,
                series_canonical_id=series_id,  # important context
            )
        if model_map:
            model_id = model_map["canonical_id"]

    return {"make_id": make_id, "series_id": series_id, "model_id": model_id}


def resolve_all_unresolved(repo: ScraperRepository, *, limit: int = 0) -> Dict[str, int]:
    """
    Resolve listings that don't have canonical ids yet.
    If limit=0 => no limit.
    """
    query = {"$or": [{"make_id": {"$exists": False}}, {"model_id": {"$exists": False}}]}
    cursor = repo.car_listings.find(query, no_cursor_timeout=True)
    if limit and limit > 0:
        cursor = cursor.limit(limit)
    

    updated = 0
    skipped = 0

    for listing in cursor:
        ids = resolve_one_listing(repo, listing)
        if ids["make_id"] and ids["model_id"]:
            repo.car_listings.update_one(
                {"_id": listing["_id"]},
                {"$set": {"make_id": ids["make_id"], "series_id": ids["series_id"], "model_id": ids["model_id"]}},
            )
            updated += 1
        else:
            skipped += 1

    return {"updated": updated, "skipped": skipped}

def update_listings_resolving(repo: ScraperRepository, *, limit: int = 0) -> None:
    """
    Update listings all listings (even resolved) with canonical ids.
    """
    cursor = repo.car_listings.find({}, no_cursor_timeout=True)
    if limit and limit > 0:
        cursor = cursor.limit(limit)

    updated = 0
    skipped = 0

    for listing in cursor:
        ids = resolve_one_listing(repo, listing)
        if ids["make_id"] and ids["model_id"]:
            repo.car_listings.update_one(
                {"_id": listing["_id"]},
                {"$set": {"make_id": ids["make_id"], "series_id": ids["series_id"], "model_id": ids["model_id"]}},
            )
            updated += 1
        else:
            skipped += 1

    return {"updated": updated, "skipped": skipped}


if __name__ == "__main__":
    repo = ScraperRepository()
    repo.connect()
    result = update_listings_resolving(repo, limit=0)
    print("Resolved listings:", result)