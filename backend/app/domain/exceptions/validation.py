from typing import List, Optional

from .base import DomainException


class ValidationError(DomainException):
    def __init__(self, message: str, field: Optional[str] = None, errors: Optional[List[str]] = None):
        self.field = field
        self.errors = errors or []
        super().__init__(message, code="VALIDATION_ERROR")


class InvalidFilterError(ValidationError):
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, field)
        self.code = "INVALID_FILTER"


class InvalidIdError(ValidationError):
    def __init__(self, entity_type: str, invalid_id: str):
        self.entity_type = entity_type
        self.invalid_id = invalid_id
        message = f"Invalid {entity_type} ID format: '{invalid_id}'"
        super().__init__(message)
        self.code = "INVALID_ID"
