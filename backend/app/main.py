import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_config
from app.infrastructure.logging import setup_logging, get_logger
from app.infrastructure.database import init_db, close_db, get_mongodb_config
from app.presentation.middlewares import (
    ErrorHandlerMiddleware,
    RequestLoggingMiddleware
)
from app.presentation.routers import listings_router, comparison_router, health_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup actions
    init_db(get_mongodb_config())
    yield
    # Shutdown actions
    close_db()
    

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    setup_logging()
    config = get_config()
    logger = get_logger(__name__)
    
    # Create FastAPI app
    app = FastAPI(
        title=config.app_name,
        description="Estonian Car Marketplace Aggregator",
        version=config.app_version,
        debug=config.debug,
        lifespan=lifespan
    )
    
    # Setup middlewares (order matters: first added = outermost)
    # Error handler should be outermost to catch all exceptions
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    
    # Setup CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(health_router)
    app.include_router(listings_router)
    app.include_router(comparison_router)
    
    # Serve static files from frontend build (for production)
    _setup_frontend_static_files(app)
    
    logger.info(f"Application started: {config.app_name} v{config.app_version}")
    
    return app


def _setup_frontend_static_files(app: FastAPI) -> None:
    """Setup static file serving for frontend (if available)."""
    # Use /app/static/frontend in Docker (outside of mounted /app/app volume)
    # Fall back to local path for development
    frontend_build_path = os.environ.get(
        "FRONTEND_BUILD_PATH",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "frontend")
    )
    
    if not os.path.exists(frontend_build_path):
        return
    
    # Mount Next.js static assets
    next_static = os.path.join(frontend_build_path, "_next")
    if os.path.exists(next_static):
        app.mount("/_next", StaticFiles(directory=next_static), name="next_static")
    
    # Serve index.html for all non-API routes (SPA routing)
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Don't intercept API routes or static assets
        if full_path.startswith("api") or full_path.startswith("_next") or full_path == "health":
            return None
        
        index_path = os.path.join(frontend_build_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"error": "Frontend not built"}


# Create the app instance
app = create_app()

