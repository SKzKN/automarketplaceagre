from typing import Dict, List, Optional

from pydantic import BaseModel

from .taxonomy_dtos import MakeDTO, SeriesDTO, ModelDTO


class PriceStats(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None
    avg: Optional[float] = None


class StatisticsResponse(BaseModel):
    total_listings: int
    by_source: Dict[str, int]
    price_stats: PriceStats
    top_makes: Dict[str, int]


class FilterOptions(BaseModel):
    makes: List[MakeDTO] = []
    series: List[SeriesDTO] = []
    models: List[ModelDTO] = []
    fuel_types: List[str] = []
    body_types: List[str] = []


class MakesFilterOptions(BaseModel):
    makes: List[MakeDTO]


class SeriesFilterOptions(BaseModel):
    series: List[SeriesDTO]


class ModelsFilterOptions(BaseModel):
    models: List[ModelDTO]

