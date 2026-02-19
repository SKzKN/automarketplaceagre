from .base import ApplicationException


class RepositoryError(ApplicationException):
    def __init__(self, message: str, original_error: Exception = None):
        self.original_error = original_error
        super().__init__(message, code="REPOSITORY_ERROR")


class ConnectionError(RepositoryError):
    def __init__(self, message: str = "Failed to connect to database", original_error: Exception = None):
        super().__init__(message, original_error)
        self.code = "CONNECTION_ERROR"


class QueryError(RepositoryError):
    def __init__(self, message: str = "Database query failed", original_error: Exception = None):
        super().__init__(message, original_error)
        self.code = "QUERY_ERROR"
