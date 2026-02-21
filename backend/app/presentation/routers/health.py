from fastapi import APIRouter
from app.infrastructure.database import get_db, get_mongodb_config

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    return {"status": "healthy"}


@router.get("/debug/db")
def debug_db():
    """Debug endpoint to check database connection and configuration."""
    try:
        config = get_mongodb_config()
        db = get_db()
        
        # Mask password in URI for security
        masked_uri = config.connection_uri
        if "@" in masked_uri:
            parts = masked_uri.split("@")
            auth_part = parts[0].split("://")[1]
            if ":" in auth_part:
                user = auth_part.split(":")[0]
                masked_uri = masked_uri.replace(auth_part, f"{user}:****")
        
        # Try to count documents
        count = db.car_listings.count_documents({})
        makes_count = db.makes.count_documents({})
        
        return {
            "status": "connected",
            "database_name": config.database_name,
            "connection_uri": masked_uri,
            "car_listings_count": count,
            "makes_count": makes_count
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }


@router.get("/api")
def api_info():
    return {
        "message": "Car Index API",
        "version": "1.0.0",
        "endpoints": {
            "listings": "/api/listings",
            "comparison": "/api/comparison",
            "health": "/health",
        },
    }
