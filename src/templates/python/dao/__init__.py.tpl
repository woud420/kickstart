"""Data Access Object (DAO) layer.

This module provides database-specific implementations for data persistence.
DAOs handle the actual database operations while repositories provide
business-domain abstractions over the DAOs.

The DAO pattern provides:
- Database-specific query implementations
- Connection and transaction management
- Result set mapping to domain entities
- Database error handling and mapping
- Performance optimizations
"""

from .base import (
    BaseDAO,
    DatabaseError,
    ConnectionError,
    QueryError,
    IntegrityError
)

__all__ = [
    # Base classes
    "BaseDAO",
    
    # Exception types  
    "DatabaseError",
    "ConnectionError",
    "QueryError", 
    "IntegrityError",
]