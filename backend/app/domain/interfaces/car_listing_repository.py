from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from app.domain.entities import CarListing
from app.domain.dtos import ListingFilters, PaginationParams, MakeDTO, SeriesDTO, ModelDTO


class ICarListingRepository(ABC):
    """
    Interface for car listing repository.
    Infrastructure layer must implement this interface.
    """
    
    @abstractmethod
    def get_by_id(self, listing_id: str) -> Optional[CarListing]:
        """Get a single listing by ID."""
        pass
    
    @abstractmethod
    def get_all(
        self,
        filters: Optional[ListingFilters] = None,
        pagination: Optional[PaginationParams] = None
    ) -> List[CarListing]:
        """Get all listings with optional filters and pagination."""
        pass
    
    @abstractmethod
    def get_by_make_and_model(
        self,
        make_id: str,
        model_id: str,
        year: Optional[int] = None
    ) -> List[CarListing]:
        """Get listings by canonical make and model IDs for comparison."""
        pass
    
    @abstractmethod
    def get_similar(
        self,
        listing: CarListing,
        limit: int = 20
    ) -> List[CarListing]:
        """Get similar listings (same make/model, different sources)."""
        pass
    
    @abstractmethod
    def count(self, filters: Optional[ListingFilters] = None) -> int:
        """Count total listings matching filters."""
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict:
        """Get overview statistics (counts, price stats, etc.)."""
        pass
    
    # ---- Taxonomy methods (canonical collections) ----
    
    @abstractmethod
    def get_all_makes(self) -> List[MakeDTO]:
        """Get all canonical makes from taxonomy."""
        pass
    
    @abstractmethod
    def get_series_for_make(self, make_id: str) -> List[SeriesDTO]:
        """Get all series for a given make from taxonomy."""
        pass
    
    @abstractmethod
    def get_models_for_make(self, make_id: str, series_id: Optional[str] = None) -> List[ModelDTO]:
        """Get all models for a given make (optionally filtered by series) from taxonomy."""
        pass
    
    @abstractmethod
    def get_distinct_fuel_types(self) -> List[str]:
        """Get list of distinct fuel types."""
        pass
    
    @abstractmethod
    def get_distinct_body_types(self) -> List[str]:
        """Get list of distinct body types."""
        pass
