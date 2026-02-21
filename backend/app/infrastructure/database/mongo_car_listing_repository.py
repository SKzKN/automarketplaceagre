from datetime import datetime
from typing import Dict, List, Optional

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.collection import Collection
from pymongo.database import Database

from app.domain.dtos import (
    ListingFilters,
    MakeDTO,
    ModelDTO,
    PaginationParams,
    SeriesDTO,
)
from app.domain.entities import CarListing
from app.domain.exceptions import InvalidIdError, QueryError
from app.domain.interfaces import ICarListingRepository
from app.infrastructure.logging import get_logger

from .mongodb_client import get_car_listings_collection, get_db

logger = get_logger(__name__)

# Taxonomy collection names (matching scraper repository)
MAKES_COL = "makes"
SERIES_COL = "series"
MODELS_COL = "models"


class MongoCarListingRepository(ICarListingRepository):
    """MongoDB implementation of ICarListingRepository."""

    def __init__(
        self,
        collection: Optional[Collection] = None,
        database: Optional[Database] = None,
    ):
        self._collection = collection
        self._database = database

    @property
    def collection(self) -> Collection:
        """Get the MongoDB collection."""
        if self._collection is None:
            self._collection = get_car_listings_collection()
        return self._collection

    @property
    def db(self) -> Database:
        """Get the MongoDB database."""
        if self._database is None:
            self._database = get_db()
        return self._database

    @property
    def makes_collection(self) -> Collection:
        """Get the makes collection."""
        return self.db[MAKES_COL]

    @property
    def series_collection(self) -> Collection:
        """Get the series collection."""
        return self.db[SERIES_COL]

    @property
    def models_collection(self) -> Collection:
        """Get the models collection."""
        return self.db[MODELS_COL]

    def get_by_id(self, listing_id: str) -> Optional[CarListing]:
        """Get a single listing by ID."""
        try:
            object_id = ObjectId(listing_id)
        except (InvalidId, TypeError):
            raise InvalidIdError("CarListing", listing_id)

        try:
            doc = self.collection.find_one({"_id": object_id})
            if not doc:
                return None
            return self._doc_to_entity(doc)
        except Exception as e:
            logger.error(f"Error getting listing by ID: {e}")
            raise QueryError(f"Failed to get listing: {e}")

    def get_all(
        self,
        filters: Optional[ListingFilters] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> List[CarListing]:
        """Get all listings with optional filters and pagination."""
        filters = filters or ListingFilters()
        pagination = pagination or PaginationParams()

        query = self._build_query(filters)

        try:
            cursor = self.collection.find(query)
            cursor = cursor.skip(pagination.offset).limit(pagination.limit)

            return [self._doc_to_entity(doc) for doc in cursor]
        except Exception as e:
            logger.error(f"Error getting listings: {e}")
            raise QueryError(f"Failed to get listings: {e}")

    def get_by_make_and_model(
        self, make_id: str, model_id: str, year: Optional[int] = None
    ) -> List[CarListing]:
        """Get listings by canonical make and model IDs for comparison."""
        try:
            make_oid = ObjectId(make_id)
            model_oid = ObjectId(model_id)
        except (InvalidId, TypeError):
            raise InvalidIdError("make_id or model_id", f"{make_id}, {model_id}")

        query = {
            "make_id": make_oid,
            "model_id": model_oid,
        }

        if year:
            query["year"] = year

        try:
            cursor = self.collection.find(query).sort([("price", 1), ("_id", 1)])
            return [self._doc_to_entity(doc) for doc in cursor]
        except Exception as e:
            logger.error(f"Error getting listings by make/model: {e}")
            raise QueryError(f"Failed to get listings: {e}")

    def get_similar(self, listing: CarListing, limit: int = 20) -> List[CarListing]:
        """Get similar listings (same make/model, different sources)."""
        if not listing.make_id or not listing.model_id:
            return []

        try:
            object_id = ObjectId(listing.id)
            make_oid = ObjectId(listing.make_id)
            model_oid = ObjectId(listing.model_id)
        except (InvalidId, TypeError):
            return []

        query = {
            "_id": {"$ne": object_id},
            "make_id": make_oid,
            "model_id": model_oid,
        }

        try:
            cursor = (
                self.collection.find(query)
                .sort([("price", 1), ("_id", 1)])
                .limit(limit)
            )
            return [self._doc_to_entity(doc) for doc in cursor]
        except Exception as e:
            logger.error(f"Error getting similar listings: {e}")
            raise QueryError(f"Failed to get similar listings: {e}")

    def count(self, filters: Optional[ListingFilters] = None) -> int:
        """Count total listings matching filters."""
        filters = filters or ListingFilters()
        query = self._build_query(filters)

        try:
            return self.collection.count_documents(query)
        except Exception as e:
            logger.error(f"Error counting listings: {e}")
            raise QueryError(f"Failed to count listings: {e}")

    def get_statistics(self) -> Dict:
        """Get overview statistics."""
        try:
            total_listings = self.collection.count_documents({})

            # Count by source
            pipeline = [
                {"$match": {"source_site": {"$ne": None}}},
                {"$group": {"_id": "$source_site", "count": {"$sum": 1}}},
            ]
            source_counts = {
                item["_id"]: item["count"]
                for item in self.collection.aggregate(pipeline)
            }

            # Price statistics
            pipeline = [
                {"$match": {"price": {"$ne": None}}},
                {
                    "$group": {
                        "_id": None,
                        "min_price": {"$min": "$price"},
                        "max_price": {"$max": "$price"},
                        "avg_price": {"$avg": "$price"},
                    }
                },
            ]
            price_result = list(self.collection.aggregate(pipeline))
            price_stats = {}
            if price_result:
                price_stats = {
                    "min": float(price_result[0].get("min_price"))
                    if price_result[0].get("min_price")
                    else None,
                    "max": float(price_result[0].get("max_price"))
                    if price_result[0].get("max_price")
                    else None,
                    "avg": float(price_result[0].get("avg_price"))
                    if price_result[0].get("avg_price")
                    else None,
                }

            # Top makes
            pipeline = [
                {"$match": {"make": {"$ne": None}}},
                {"$group": {"_id": "$make", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10},
            ]
            make_counts = {
                item["_id"]: item["count"]
                for item in self.collection.aggregate(pipeline)
            }

            return {
                "total_listings": total_listings,
                "by_source": source_counts,
                "price_stats": price_stats,
                "top_makes": make_counts,
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            raise QueryError(f"Failed to get statistics: {e}")

    # ---- Taxonomy methods (canonical collections) ----

    def get_all_makes(self) -> List[MakeDTO]:
        """Get makes that have actual car listings, with top brands first."""
        try:
            # Get distinct make_ids from actual car listings
            make_ids_with_listings = self.collection.distinct("make_id", {"make_id": {"$ne": None}})
            
            if not make_ids_with_listings:
                return []
            
            # Get make details from taxonomy for makes that have listings
            cursor = self.makes_collection.find({
                "_id": {"$in": make_ids_with_listings}
            }).sort([("is_top", -1), ("name_et", 1)])
            
            return [
                MakeDTO(
                    id=str(doc["_id"]),
                    name=doc.get("name_et", ""),
                    is_top=doc.get("is_top", False),
                )
                for doc in cursor
            ]
        except Exception as e:
            logger.error(f"Error getting all makes: {e}")
            raise QueryError(f"Failed to get makes: {e}")

    def get_series_for_make(self, make_id: str) -> List[SeriesDTO]:
        """Get series for a given make that have actual car listings."""
        try:
            make_oid = ObjectId(make_id)
        except (InvalidId, TypeError):
            raise InvalidIdError("make_id", make_id)

        try:
            # Get distinct series_ids from actual car listings for this make
            series_ids_with_listings = self.collection.distinct(
                "series_id", 
                {"make_id": make_oid, "series_id": {"$ne": None}}
            )
            
            if not series_ids_with_listings:
                return []
            
            # Get series details from taxonomy
            cursor = self.series_collection.find({
                "_id": {"$in": series_ids_with_listings}
            }).sort("name_et", 1)
            
            return [
                SeriesDTO(
                    id=str(doc["_id"]),
                    name=doc.get("name_et", ""),
                    make_id=str(doc["make_id"]),
                )
                for doc in cursor
            ]
        except Exception as e:
            logger.error(f"Error getting series for make: {e}")
            raise QueryError(f"Failed to get series: {e}")

    def get_models_for_make(
        self, make_id: str, series_id: Optional[str] = None
    ) -> List[ModelDTO]:
        """Get models for a given make that have actual car listings."""
        try:
            make_oid = ObjectId(make_id)
        except (InvalidId, TypeError):
            raise InvalidIdError("make_id", make_id)

        # First, get distinct model_ids from actual car listings
        listings_query: Dict = {
            "make_id": make_oid,
            "model_id": {"$ne": None}
        }
        
        if series_id:
            try:
                series_oid = ObjectId(series_id)
                listings_query["series_id"] = series_oid
            except (InvalidId, TypeError):
                raise InvalidIdError("series_id", series_id)

        try:
            # Get model_ids that actually have listings
            model_ids_with_listings = self.collection.distinct("model_id", listings_query)
            
            if not model_ids_with_listings:
                return []
            
            # Look up model details from taxonomy
            cursor = self.models_collection.find({
                "_id": {"$in": model_ids_with_listings}
            }).sort("name_et", 1)
            
            return [
                ModelDTO(
                    id=str(doc["_id"]),
                    name=doc.get("name_et", ""),
                    make_id=str(doc["make_id"]),
                    series_id=str(doc["series_id"]) if doc.get("series_id") else None,
                )
                for doc in cursor
            ]
        except Exception as e:
            logger.error(f"Error getting models for make: {e}")
            raise QueryError(f"Failed to get models: {e}")

    def get_distinct_fuel_types(self) -> List[str]:
        """Get list of distinct fuel types."""
        try:
            pipeline = [
                {"$match": {"fuel_type": {"$nin": [None, ""]}}},
                {"$group": {"_id": "$fuel_type"}},
                {"$sort": {"_id": 1}},
            ]
            return [item["_id"] for item in self.collection.aggregate(pipeline)]
        except Exception as e:
            logger.error(f"Error getting distinct fuel types: {e}")
            raise QueryError(f"Failed to get fuel types: {e}")

    def get_distinct_body_types(self) -> List[str]:
        """Get list of distinct body types."""
        try:
            pipeline = [
                {"$match": {"body_type": {"$nin": [None, ""]}}},
                {"$group": {"_id": "$body_type"}},
                {"$sort": {"_id": 1}},
            ]
            return [item["_id"] for item in self.collection.aggregate(pipeline)]
        except Exception as e:
            logger.error(f"Error getting distinct body types: {e}")
            raise QueryError(f"Failed to get body types: {e}")

    def _build_query(self, filters: ListingFilters) -> Dict:
        """Build MongoDB query from filters."""
        query: Dict = {}

        # Filter out listings with no source_site
        query["source_site"] = {"$ne": None}

        # Text search
        if filters.query:
            query["$or"] = [
                {"title": {"$regex": filters.query, "$options": "i"}},
                {"make": {"$regex": filters.query, "$options": "i"}},
                {"model": {"$regex": filters.query, "$options": "i"}},
                {"description": {"$regex": filters.query, "$options": "i"}},
            ]

        # Canonical ID-based filters (hierarchical)
        if filters.make_id:
            try:
                query["make_id"] = ObjectId(filters.make_id)
            except (InvalidId, TypeError):
                pass  # Invalid ID, skip filter

        if filters.series_id:
            try:
                query["series_id"] = ObjectId(filters.series_id)
            except (InvalidId, TypeError):
                pass

        if filters.model_id:
            try:
                query["model_id"] = ObjectId(filters.model_id)
            except (InvalidId, TypeError):
                pass

        if filters.min_price is not None or filters.max_price is not None:
            query["price"] = {}
            if filters.min_price is not None:
                query["price"]["$gte"] = filters.min_price
            if filters.max_price is not None:
                query["price"]["$lte"] = filters.max_price

        if filters.min_year is not None or filters.max_year is not None:
            query["year"] = {}
            if filters.min_year is not None:
                query["year"]["$gte"] = filters.min_year
            if filters.max_year is not None:
                query["year"]["$lte"] = filters.max_year

        if filters.body_type:
            query["body_type"] = filters.body_type

        if filters.fuel_type:
            query["fuel_type"] = filters.fuel_type

        if filters.source_site:
            query["source_site"] = filters.source_site

        return query

    def _doc_to_entity(self, doc: Dict) -> CarListing:
        """Convert MongoDB document to CarListing entity."""
        return CarListing(
            id=str(doc["_id"]),
            title=doc.get("title", ""),
            source_url=doc.get("source_url", ""),
            source_site=doc.get("source_site"),
            # Display names
            make=doc.get("make"),
            series=doc.get("series"),
            model=doc.get("model"),
            # Canonical IDs (convert ObjectId to str)
            make_id=str(doc["make_id"]) if doc.get("make_id") else None,
            series_id=str(doc["series_id"]) if doc.get("series_id") else None,
            model_id=str(doc["model_id"]) if doc.get("model_id") else None,
            # Vehicle details
            year=doc.get("year"),
            price=doc.get("price"),
            mileage=doc.get("mileage"),
            fuel_type=doc.get("fuel_type"),
            transmission=doc.get("transmission"),
            body_type=doc.get("body_type"),
            color=doc.get("color"),
            description=doc.get("description"),
            image_url=doc.get("image_url"),
            created_at=doc.get("created_at") or datetime.utcnow(),
            updated_at=doc.get("updated_at") or datetime.utcnow(),
        )
