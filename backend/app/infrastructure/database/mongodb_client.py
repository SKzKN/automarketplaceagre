from typing import Optional

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from app.infrastructure.logging import get_logger
from .config import MongoDBConfig


logger = get_logger(__name__)


class MongoDBClient:
    """MongoDB client wrapper with connection management."""
    
    _instance: Optional["MongoDBClient"] = None
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def connect(self, uri: Optional[str] = None, database_name: Optional[str] = None) -> None:
        if self._client is not None:
            return
        
        # Create MongoClient with explicit TLS settings for MongoDB Atlas
        self._client = MongoClient(
            uri,
            tls=True,
            tlsAllowInvalidCertificates=False,
            serverSelectionTimeoutMS=30000,
        )
        self._db = self._client.get_database(database_name)
        self._ensure_indexes()
        
        logger.info(f"Connected to MongoDB database: {database_name}")
    
    def disconnect(self) -> None:
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("Disconnected from MongoDB")
    
    def _ensure_indexes(self) -> None:
        if self._db is not None:
            car_listings = self._db["car_listings"]
            car_listings.create_index("source_url", unique=True)
            car_listings.create_index("source_site")
            car_listings.create_index("make")
            car_listings.create_index("model")
            car_listings.create_index("price")
            car_listings.create_index("year")
            car_listings.create_index([
                ("title", "text"),
                ("make", "text"),
                ("model", "text"),
                ("description", "text")
            ])
            
            # Canonical ID indexes for filtering
            car_listings.create_index("make_id")
            car_listings.create_index("series_id")
            car_listings.create_index("model_id")
            car_listings.create_index([("make_id", 1), ("series_id", 1), ("model_id", 1)])

            # Taxonomy collections (indexes must match scraper's schema - snake_case)
            makes = self._db["makes"]
            makes.create_index("norm", unique=True)

            series = self._db["series"]
            series.create_index([("make_id", 1), ("norm", 1)], unique=True)
            series.create_index("make_id")

            models = self._db["models"]
            models.create_index([("make_id", 1), ("series_id", 1), ("norm", 1)], unique=True)
            models.create_index([("make_id", 1), ("series_id", 1)])

            mappings = self._db["taxonomy_mappings"]
            mappings.create_index([("source_site", 1), ("entity_type", 1), ("make_canonical_id", 1), ("series_canonical_id", 1), ("source_norm", 1)], unique=True)
            mappings.create_index([("source_site", 1), ("entity_type", 1), ("make_canonical_id", 1), ("source_key", 1)])
    
    @property
    def database(self) -> Database:
        """Get the database instance."""
        if self._db is None:
            self.connect()
        return self._db  # type: ignore
    
    def get_collection(self, name: str) -> Collection:
        """Get a collection by name."""
        return self.database[name]
    
    @property
    def car_listings(self) -> Collection:
        """Get the car_listings collection."""
        return self.get_collection("car_listings")


# Module-level functions for convenience
_client: Optional[MongoDBClient] = None

def init_db(config: MongoDBConfig) -> None:
    """Initialize database connection."""
    global _client
    if not _client:
        _client = MongoDBClient(
        )
        _client.connect(uri=config.connection_uri, database_name=config.database_name)

def get_db() -> Database:
    """Get the database instance."""
    global _client
    if _client is None:
        _client = MongoDBClient()
        _client.connect()
    return _client.database

def get_car_listings_collection() -> Collection:
    """Get the car_listings collection."""
    global _client
    if _client is None:
        _client = MongoDBClient()
        _client.connect()
    return _client.car_listings

def close_db() -> None:
    """Close database connection."""
    global _client
    if _client:
        _client.disconnect()
        _client = None
