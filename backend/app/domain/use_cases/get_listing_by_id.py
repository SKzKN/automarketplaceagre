from app.domain.dtos import CarListingResponse
from app.domain.exceptions import EntityNotFoundError, InvalidIdError
from app.domain.interfaces import ICarListingRepository


class GetListingByIdUseCase:
    """Use case for retrieving a single car listing by ID."""
    
    def __init__(self, repository: ICarListingRepository):
        self._repository = repository
    
    def execute(self, listing_id: str) -> CarListingResponse:
        if not listing_id or not listing_id.strip():
            raise InvalidIdError("CarListing", listing_id or "")
        
        listing = self._repository.get_by_id(listing_id)
        
        if not listing:
            raise EntityNotFoundError("CarListing", listing_id)
        
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
