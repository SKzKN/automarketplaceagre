from app.domain.dtos import StatisticsResponse, PriceStats
from app.domain.interfaces import ICarListingRepository


class GetStatisticsUseCase:
    """Use case for retrieving statistics overview."""
    
    def __init__(self, repository: ICarListingRepository):
        self._repository = repository
    
    def execute(self) -> StatisticsResponse:
        stats = self._repository.get_statistics()
        
        price_stats_data = stats.get('price_stats', {})
        
        return StatisticsResponse(
            total_listings=stats.get('total_listings', 0),
            by_source=stats.get('by_source', {}),
            price_stats=PriceStats(
                min=price_stats_data.get('min'),
                max=price_stats_data.get('max'),
                avg=price_stats_data.get('avg'),
            ),
            top_makes=stats.get('top_makes', {}),
        )
