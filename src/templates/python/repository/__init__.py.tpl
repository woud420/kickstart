"""Repository layer for data access abstraction.

This module exports the repository classes that provide business-domain
specific data access operations. Repositories use composition with DAO
objects to perform actual data persistence while keeping business logic
separate from database implementation details.

The Repository pattern provides:
- Abstraction over data storage
- Testability through dependency injection  
- Business-domain specific query methods
- Consistent error handling
- Type-safe operations with generics
"""

from .base import (
    BaseRepository,
    QueryFilter,
    QueryOptions,
    RepositoryError,
    ValidationError,
    ConcurrencyError
)
from .user_repo import UserRepository

__all__ = [
    # Base classes and utilities
    "BaseRepository",
    "QueryFilter", 
    "QueryOptions",
    
    # Exception types
    "RepositoryError",
    "ValidationError",
    "ConcurrencyError",
    
    # Repository implementations
    "UserRepository",
]