from typing import List, Optional

from app.domain.dtos import MakeDTO, SeriesDTO, ModelDTO
from app.domain.interfaces import ICarListingRepository


class GetFilterOptionsUseCase:
    """Use case for retrieving filter options from canonical taxonomy."""
    
    def __init__(self, repository: ICarListingRepository):
        self._repository = repository
    
    def get_makes(self) -> List[MakeDTO]:
        return self._repository.get_all_makes()
    
    def get_series(self, make_id: str) -> List[SeriesDTO]:
        return self._repository.get_series_for_make(make_id)
    
    def get_models(self, make_id: str, series_id: Optional[str] = None) -> List[ModelDTO]:
        return self._repository.get_models_for_make(make_id, series_id)
    
    def get_fuel_types(self) -> List[str]:
        return sorted(self._repository.get_distinct_fuel_types())
    
    def get_body_types(self) -> List[str]:
        return sorted(self._repository.get_distinct_body_types())
