from .base import DomainException


class EntityNotFoundError(DomainException):
    def __init__(self, entity_type: str, entity_id: str):
        self.entity_type = entity_type
        self.entity_id = entity_id
        message = f"{entity_type} with id '{entity_id}' not found"
        super().__init__(message, code="ENTITY_NOT_FOUND")


class DuplicateEntityError(DomainException):
    def __init__(self, entity_type: str, identifier: str):
        self.entity_type = entity_type
        self.identifier = identifier
        message = f"{entity_type} with identifier '{identifier}' already exists"
        super().__init__(message, code="DUPLICATE_ENTITY")


class InvalidEntityError(DomainException):
    def __init__(self, entity_type: str, reason: str):
        self.entity_type = entity_type
        self.reason = reason
        message = f"Invalid {entity_type}: {reason}"
        super().__init__(message, code="INVALID_ENTITY")
