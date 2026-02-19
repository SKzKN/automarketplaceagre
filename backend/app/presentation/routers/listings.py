from typing import List, Optional

from fastapi import APIRouter, Query

from app.domain.dtos import (
    CarListingResponse,
    ListingFilters,
    MakeDTO,
    ModelDTO,
    PaginationParams,
    SeriesDTO,
)
from app.presentation.dependencies import (
    GetFilterOptionsUseCaseDependency,
    GetListingByIdUseCaseDependency,
    GetListingsUseCaseDependency,
    GetStatisticsUseCaseDependency,
)

router = APIRouter(prefix="/api/listings", tags=["listings"])


@router.get("/", response_model=List[CarListingResponse])
def get_listings(
    use_case: GetListingsUseCaseDependency,
    query: Optional[str] = Query(
        None, description="Search query (searches in title, make, model)"
    ),
    make_id: Optional[str] = Query(None, description="Canonical make ID"),
    series_id: Optional[str] = Query(
        None, description="Canonical series ID (requires make_id)"
    ),
    model_id: Optional[str] = Query(
        None, description="Canonical model ID (requires make_id)"
    ),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    min_year: Optional[int] = Query(None),
    max_year: Optional[int] = Query(None),
    body_type: Optional[str] = Query(None),
    fuel_type: Optional[str] = Query(None),
    source_site: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    filters = ListingFilters(
        query=query,
        make_id=make_id,
        series_id=series_id,
        model_id=model_id,
        min_price=min_price,
        max_price=max_price,
        min_year=min_year,
        max_year=max_year,
        body_type=body_type,
        fuel_type=fuel_type,
        source_site=source_site,
    )
    pagination = PaginationParams(limit=limit, offset=offset)

    return use_case.execute(filters=filters, pagination=pagination)


@router.get("/stats/overview")
def get_stats(
    use_case: GetStatisticsUseCaseDependency,
):
    return use_case.execute()


@router.get("/filter-options/makes", response_model=List[MakeDTO])
def get_makes(
    use_case: GetFilterOptionsUseCaseDependency,
):
    return use_case.get_makes()


@router.get("/filter-options/series/{make_id}", response_model=List[SeriesDTO])
def get_series(
    make_id: str,
    use_case: GetFilterOptionsUseCaseDependency,
):
    return use_case.get_series(make_id)


@router.get("/filter-options/models/{make_id}", response_model=List[ModelDTO])
def get_models(
    make_id: str,
    use_case: GetFilterOptionsUseCaseDependency,
    series_id: Optional[str] = Query(None, description="Filter models by series ID"),
):
    return use_case.get_models(make_id, series_id)


@router.get("/filter-options/fuel-types")
def get_fuel_types(
    use_case: GetFilterOptionsUseCaseDependency,
):
    fuel_types = use_case.get_fuel_types()
    return {"fuel_types": fuel_types}


@router.get("/filter-options/body-types")
def get_body_types(
    use_case: GetFilterOptionsUseCaseDependency,
):
    body_types = use_case.get_body_types()
    return {"body_types": body_types}


@router.get("/{listing_id}", response_model=CarListingResponse)
def get_listing(
    listing_id: str,
    use_case: GetListingByIdUseCaseDependency,
):
    return use_case.execute(listing_id)
