import traceback
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.domain.exceptions import (
    DomainException,
    ApplicationException,
    EntityNotFoundError,
    DuplicateEntityError,
    InvalidEntityError,
    ValidationError,
    InvalidFilterError,
    InvalidIdError,
    RepositoryError,
    ConnectionError,
    QueryError,
)
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for handling exceptions globally."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            return self._handle_exception(exc, request)
    
    def _handle_exception(self, exc: Exception, request: Request) -> JSONResponse:
        """Handle exception and return appropriate JSON response."""
        
        # Log the error with request context
        log_context = {
            "path": request.url.path,
            "method": request.method,
            "client_ip": request.client.host if request.client else "unknown",
        }
        
        # Map exceptions to HTTP status codes
        if isinstance(exc, EntityNotFoundError):
            logger.warning(f"Entity not found: {exc.message}", extra=log_context)
            return self._error_response(404, exc.code, exc.message)
        
        if isinstance(exc, (InvalidIdError, InvalidFilterError)):
            logger.warning(f"Validation error: {exc.message}", extra=log_context)
            return self._error_response(400, exc.code, exc.message)
        
        if isinstance(exc, ValidationError):
            logger.warning(f"Validation error: {exc.message}", extra=log_context)
            return self._error_response(400, exc.code, exc.message, field=exc.field)
        
        if isinstance(exc, DuplicateEntityError):
            logger.warning(f"Duplicate entity: {exc.message}", extra=log_context)
            return self._error_response(409, exc.code, exc.message)
        
        if isinstance(exc, InvalidEntityError):
            logger.warning(f"Invalid entity: {exc.message}", extra=log_context)
            return self._error_response(422, exc.code, exc.message)
        
        if isinstance(exc, ConnectionError):
            logger.error(f"Database connection error: {exc.message}", extra=log_context)
            return self._error_response(503, exc.code, "Service temporarily unavailable")
        
        if isinstance(exc, (QueryError, RepositoryError)):
            logger.error(f"Repository error: {exc.message}", extra=log_context)
            return self._error_response(500, exc.code, "Internal server error")
        
        if isinstance(exc, (DomainException, ApplicationException)):
            logger.error(f"Domain/Application error: {exc.message}", extra=log_context)
            return self._error_response(500, exc.code, exc.message)
        
        # Unexpected errors
        logger.error(
            f"Unexpected error: {str(exc)}\n{traceback.format_exc()}",
            extra=log_context
        )
        return self._error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
    
    @staticmethod
    def _error_response(
        status_code: int,
        error_code: str,
        message: str,
        **kwargs
    ) -> JSONResponse:
        """Create a standardized error response."""
        content = {
            "error": {
                "code": error_code,
                "message": message,
                **kwargs
            }
        }
        return JSONResponse(status_code=status_code, content=content)
