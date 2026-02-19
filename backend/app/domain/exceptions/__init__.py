"""
Domain exceptions.
All exceptions are defined here and can be imported from this package.
"""
from .base import (
    DomainException,
    ApplicationException,
)
from .entity import (
    EntityNotFoundError,
    DuplicateEntityError,
    InvalidEntityError,
)
from .repository import (
    RepositoryError,
    ConnectionError,
    QueryError,
)
from .validation import (
    ValidationError,
    InvalidFilterError,
    InvalidIdError,
)

__all__ = [
    # Base
    'DomainException',
    'ApplicationException',
    # Entity
    'EntityNotFoundError',
    'DuplicateEntityError',
    'InvalidEntityError',
    # Repository
    'RepositoryError',
    'ConnectionError',
    'QueryError',
    # Validation
    'ValidationError',
    'InvalidFilterError',
    'InvalidIdError',
]
