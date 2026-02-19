from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    return {"status": "healthy"}


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
