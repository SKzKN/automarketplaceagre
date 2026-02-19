from typing import List, Optional

from app.domain.dtos import CarListingResponse
from app.domain.exceptions import EntityNotFoundError, ValidationError
from app.domain.interfaces import ICarListingRepository


class CompareCarsUseCase:
    """Use case for comparing similar cars from different sources."""
    
    def __init__(self, repository: ICarListingRepository):
        self._repository = repository
    
    def execute(
        self,
        make_id: str,
        model_id: str,
        year: Optional[int] = None
    ) -> List[CarListingResponse]:
        if not make_id or not make_id.strip():
            raise ValidationError("make_id is required", field="make_id")
        
        if not model_id or not model_id.strip():
            raise ValidationError("model_id is required", field="model_id")
        
        listings = self._repository.get_by_make_and_model(make_id, model_id, year)
        
        if not listings:
            raise EntityNotFoundError(
                "CarListing", 
                f"make_id={make_id}, model_id={model_id}" + (f", year={year}" if year else "")
            )
        
        # Sort by price (ascending)
        listings.sort(key=lambda x: (x.price is None, x.price or 0))
        
        return [self._to_response(listing) for listing in listings]
    
    def get_similar(self, listing_id: str, limit: int = 20) -> List[CarListingResponse]:
        listing = self._repository.get_by_id(listing_id)
        
        if not listing:
            raise EntityNotFoundError("CarListing", listing_id)
        
        if not listing.make_id or not listing.model_id:
            return []
        
        similar_listings = self._repository.get_similar(listing, limit)
        
        # Sort by price
        similar_listings.sort(key=lambda x: (x.price is None, x.price or 0))
        
        return [self._to_response(item) for item in similar_listings]
    
    @staticmethod
    def _to_response(listing) -> CarListingResponse:
        """Convert entity to response DTO."""
        return CarListingResponse(
            id=listing.id,
            title=listing.title,
            make=listing.make,
            series=listing.series,
            model=listing.model,
            make_id=listing.make_id,
            series_id=listing.series_id,
            model_id=listing.model_id,
            year=listing.year,
            price=listing.price,
            mileage=listing.mileage,
            fuel_type=listing.fuel_type,
            transmission=listing.transmission,
            body_type=listing.body_type,
            color=listing.color,
            description=listing.description,
            image_url=listing.image_url,
            source_url=listing.source_url,
            source_site=listing.source_site,
            created_at=listing.created_at,
            updated_at=listing.updated_at,
        )
