"""Service layer exception classes.

This module defines the exception hierarchy for the service layer,
providing specific error types for different failure scenarios.
"""


class ServiceError(Exception):
    """Base exception for service layer operations."""
    pass


class ValidationError(ServiceError):
    """Raised when business rule validation fails."""
    pass


class NotFoundError(ServiceError):
    """Raised when a requested entity is not found."""
    pass


class ConflictError(ServiceError):
    """Raised when an operation conflicts with current state."""
    pass


class PermissionError(ServiceError):
    """Raised when user lacks permission for an operation."""
    pass


class BusinessRuleError(ServiceError):
    """Raised when business rules are violated."""
    pass


class ExternalServiceError(ServiceError):
    """Raised when external service operations fail."""
    pass