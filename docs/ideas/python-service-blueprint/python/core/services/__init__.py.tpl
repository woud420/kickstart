"""Service layer for business logic operations.

This module contains business services that coordinate between repositories,
validate business rules, and handle complex operations that span multiple
domain entities.

Services provide:
- Business logic coordination
- Transaction management
- Validation orchestration  
- Cross-repository operations
- Business rule enforcement
- External service integration
"""

from .base_service import BaseService
from .user_service import UserService
from .exceptions import (
    ServiceError,
    ValidationError,
    NotFoundError,
    ConflictError,
    PermissionError,
    BusinessRuleError,
    ExternalServiceError
)

__all__ = [
    # Base classes
    "BaseService",
    
    # Service implementations
    "UserService",
    
    # Exception types
    "ServiceError",
    "ValidationError",
    "NotFoundError",
    "ConflictError", 
    "PermissionError",
    "BusinessRuleError",
    "ExternalServiceError",
]