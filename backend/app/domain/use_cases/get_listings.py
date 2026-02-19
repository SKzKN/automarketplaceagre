import random
from typing import List

from app.domain.dtos import CarListingResponse, ListingFilters, PaginationParams
from app.domain.interfaces import ICarListingRepository


class GetListingsUseCase:
    """Use case for retrieving car listings."""
    
    def __init__(self, repository: ICarListingRepository):
        self._repository = repository
    
    def execute(
        self,
        filters: ListingFilters = None,
        pagination: PaginationParams = None,
        randomize: bool = True
    ) -> List[CarListingResponse]:
        filters = filters or ListingFilters()
        pagination = pagination or PaginationParams()
        
        listings = self._repository.get_all(filters, pagination)
        
        if randomize:
            random.shuffle(listings)
        
        return [
            CarListingResponse(
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
            for listing in listings
        ]
