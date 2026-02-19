from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CarListing(BaseModel):
    id: str
    title: str
    source_url: str
    source_site: Optional[str] = None

    # Display names (from scraper)
    make: Optional[str] = None
    series: Optional[str] = None
    model: Optional[str] = None

    # Canonical IDs (resolved from taxonomy)
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
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    def has_complete_info(self) -> bool:
        return all([
            self.make,
            self.model,
            self.year,
            self.price
        ])
    
    def matches_search(self, make_id: Optional[str] = None, series_id: Optional[str] = None, model_id: Optional[str] = None) -> bool:
        if make_id and self.make_id != make_id:
            return False
        if series_id and self.series_id != series_id:
            return False
        if model_id and self.model_id != model_id:
            return False
        return True
