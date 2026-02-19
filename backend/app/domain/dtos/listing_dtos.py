from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CarListingResponse(BaseModel):
    id: str
    title: str
    # Display names
    make: Optional[str] = None
    series: Optional[str] = None
    model: Optional[str] = None
    # Canonical IDs
    make_id: Optional[str] = None
    series_id: Optional[str] = None
    model_id: Optional[str] = None
    # Vehicle details
    year: Optional[int] = None
    price: Optional[float] = None
    mileage: Optional[int] = None
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    body_type: Optional[str] = None
    color: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    source_url: str
    source_site: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        orm_mode=True,
        extra="ignore"
    )


class CarListingCreateRequest(BaseModel):
    title: str
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    price: Optional[float] = None
    mileage: Optional[int] = None
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    body_type: Optional[str] = None
    color: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    source_url: str
    source_site: Optional[str] = None



class ListingFilters(BaseModel):
    query: Optional[str] = None
    # Canonical ID-based filters (hierarchical)
    make_id: Optional[str] = None
    series_id: Optional[str] = None
    model_id: Optional[str] = None
    # Price and year ranges
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_year: Optional[int] = None
    max_year: Optional[int] = None
    # Other filters
    body_type: Optional[str] = None
    fuel_type: Optional[str] = None
    source_site: Optional[str] = None


class PaginationParams(BaseModel):
    limit: int = 50
    offset: int = 0
    
    def __post_init__(self):
        if self.limit < 1:
            self.limit = 1
        if self.limit > 100:
            self.limit = 100
        if self.offset < 0:
            self.offset = 0
