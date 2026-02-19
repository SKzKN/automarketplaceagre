import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""
    
    # Paths to skip logging (health checks, etc.)
    SKIP_PATHS = {"/health", "/favicon.ico"}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip logging for certain paths
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)
        
        # Start timing
        start_time = time.time()
        
        # Get request info
        method = request.method
        path = request.url.path
        query = str(request.query_params) if request.query_params else ""
        client_ip = request.client.host if request.client else "unknown"
        
        # Log incoming request
        logger.info(
            f"→ {method} {path}",
            extra={
                "request_method": method,
                "request_path": path,
                "query_string": query,
                "client_ip": client_ip,
            }
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Determine log level based on status code
        status_code = response.status_code
        if status_code >= 500:
            log_func = logger.error
        elif status_code >= 400:
            log_func = logger.warning
        else:
            log_func = logger.info
        
        # Log response
        log_func(
            f"← {method} {path} {status_code} ({duration_ms:.2f}ms)",
            extra={
                "request_method": method,
                "request_path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "client_ip": client_ip,
            }
        )
        
        return response
