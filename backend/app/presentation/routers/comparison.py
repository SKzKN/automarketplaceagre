from typing import List, Optional

from fastapi import APIRouter, Query

from app.domain.dtos import CarListingResponse
from app.presentation.dependencies import CompareCarsUseCaseDependency

router = APIRouter(prefix="/api/comparison", tags=["comparison"])


@router.get("/compare", response_model=List[CarListingResponse])
def compare_cars(
    use_case: CompareCarsUseCaseDependency,
    make_id: str = Query(..., description="Canonical make ID"),
    model_id: str = Query(..., description="Canonical model ID"),
    year: Optional[int] = Query(None, description="Optional year filter"),
):
    return use_case.execute(make_id=make_id, model_id=model_id, year=year)


@router.get("/similar/{listing_id}", response_model=List[CarListingResponse])
def get_similar_cars(
    listing_id: str,
    use_case: CompareCarsUseCaseDependency,
):
    return use_case.get_similar(listing_id)
