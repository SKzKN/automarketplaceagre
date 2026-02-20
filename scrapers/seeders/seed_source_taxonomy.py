from typing import Dict, Iterable, Optional, Protocol

from bson import ObjectId

from scrapers.repository import ScraperRepository, clean_label
from .models import SourceMake

class SourceTaxonomyExtractor(Protocol):
    """
    You implement this per source: veego/autodiiler.
    It must yield SourceMake entries (one per make).
    """
    source_site: str

    def iter_makes(self) -> Iterable[SourceMake]:
        ...


# ---------- Canonical resolver policy

def resolve_or_create_make(repo: ScraperRepository, make_label: str) -> ObjectId:
    """
    For first phase we allow creating canonical makes if missing.
    In practice: your canonical base is from auto24, so it should exist,
    but for safety we upsert.
    """
    return repo.upsert_make(name_et=make_label)


def resolve_or_create_series(repo: ScraperRepository, make_id: ObjectId, series_label: str) -> ObjectId:
    return repo.upsert_series(make_id=make_id, name_et=series_label)


def resolve_or_create_model(repo: ScraperRepository, make_id: ObjectId, series_id: Optional[ObjectId], model_label: str) -> ObjectId:
    return repo.upsert_model(make_id=make_id, name_et=model_label, series_id=series_id)


# ---------- Seeding logic (generic)

def seed_source_taxonomy(
    repo: ScraperRepository,
    extractor: SourceTaxonomyExtractor,
) -> Dict[str, int]:
    """
    Build taxonomy_mappings for one source (veego/autodiiler).

    Strategy:
    - for each make/series/model from source:
        1) resolve/create canonical entity (by label)
        2) upsert mapping:
            - by source_key (id) if provided
            - and ALWAYS store source_label/source_norm for debugging/fallback
    """
    counters = {"makes": 0, "series": 0, "models": 0, "mappings": 0}

    for m in extractor.iter_makes():
        make_label = clean_label(m.label)
        make_id = resolve_or_create_make(repo, make_label)
        counters["makes"] += 1

        # Addding mapping for make
        repo.upsert_mapping(
            source_site=extractor.source_site,
            entity_type="make",
            source_label=m.label,
            canonical_id=make_id,
            make_canonical_id=None,
            series_canonical_id=None,
            source_key=str(m.source_make_id) if m.source_make_id is not None else None,
            method="seed_source_taxonomy",
            extra={"level": "make"},
        )
        counters["mappings"] += 1

        # Models directly under make (no series)
        for mdl in m.models_no_series:
            model_label = clean_label(mdl.label)
            model_id = resolve_or_create_model(repo, make_id, None, model_label)
            counters["models"] += 1

            repo.upsert_mapping(
                source_site=extractor.source_site,
                entity_type="model",
                source_label=mdl.label,
                canonical_id=model_id,
                make_canonical_id=make_id,
                series_canonical_id=None,
                source_key=str(mdl.source_model_id) if mdl.source_model_id is not None else None,
                method="seed_source_taxonomy",
                extra={"level": "model", "kind": "model_no_series"},
            )
            counters["mappings"] += 1

        # Series + models in series
        for s in m.series:
            series_label = clean_label(s.label)
            series_id = resolve_or_create_series(repo, make_id, series_label)
            counters["series"] += 1

            repo.upsert_mapping(
                source_site=extractor.source_site,
                entity_type="series",
                source_label=s.label,
                canonical_id=series_id,
                make_canonical_id=make_id,
                series_canonical_id=None,
                source_key=str(s.source_series_id) if s.source_series_id is not None else None,
                method="seed_source_taxonomy",
                extra={"level": "series"},
            )
            counters["mappings"] += 1

            for mdl in s.models:
                model_label = clean_label(mdl.label)
                model_id = resolve_or_create_model(repo, make_id, series_id, model_label)
                counters["models"] += 1

                repo.upsert_mapping(
                    source_site=extractor.source_site,
                    entity_type="model",
                    source_label=mdl.label,
                    canonical_id=model_id,
                    make_canonical_id=make_id,
                    series_canonical_id=series_id,
                    source_key=str(mdl.source_model_id) if mdl.source_model_id is not None else None,
                    method="seed_source_taxonomy",
                    extra={"level": "model", "kind": "in_series"},
                )
                counters["mappings"] += 1

    return counters
