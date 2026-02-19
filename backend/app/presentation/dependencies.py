from fastapi import Depends

from functools import lru_cache

from app.domain.interfaces import ICarListingRepository
from app.domain.use_cases import (
    GetListingsUseCase,
    GetListingByIdUseCase,
    GetStatisticsUseCase,
    CompareCarsUseCase,
    GetFilterOptionsUseCase,
)
from app.infrastructure.database import MongoCarListingRepository
from typing import Annotated

@lru_cache()
def get_repository() -> ICarListingRepository:
    """Get the car listing repository instance."""
    return MongoCarListingRepository()


def get_listings_use_case(repository: "CarListingsRepositoryDependency") -> GetListingsUseCase:
    """Get the GetListingsUseCase instance."""
    return GetListingsUseCase(repository=repository)


def get_listing_by_id_use_case(repository: "CarListingsRepositoryDependency") -> GetListingByIdUseCase:
    """Get the GetListingByIdUseCase instance."""
    return GetListingByIdUseCase(repository=repository)


def get_statistics_use_case(repository: "CarListingsRepositoryDependency") -> GetStatisticsUseCase:
    """Get the GetStatisticsUseCase instance."""
    return GetStatisticsUseCase(repository=repository)


def get_compare_cars_use_case(repository: "CarListingsRepositoryDependency") -> CompareCarsUseCase:
    """Get the CompareCarsUseCase instance."""
    return CompareCarsUseCase(repository=repository)


def get_filter_options_use_case(repository: "CarListingsRepositoryDependency") -> GetFilterOptionsUseCase:
    """Get the GetFilterOptionsUseCase instance."""
    return GetFilterOptionsUseCase(repository=repository)


# Type annotations for FastAPI dependencies
CarListingsRepositoryDependency = Annotated[ICarListingRepository, Depends(get_repository)]
GetListingsUseCaseDependency = Annotated[GetListingsUseCase, Depends(get_listings_use_case)]
GetListingByIdUseCaseDependency = Annotated[GetListingByIdUseCase, Depends(get_listing_by_id_use_case)]
GetStatisticsUseCaseDependency = Annotated[GetStatisticsUseCase, Depends(get_statistics_use_case)]
CompareCarsUseCaseDependency = Annotated[CompareCarsUseCase, Depends(get_compare_cars_use_case)]
GetFilterOptionsUseCaseDependency = Annotated[GetFilterOptionsUseCase, Depends(get_filter_options_use_case)]
