"""Base repository pattern with generic type support.

This module provides the abstract base repository class that defines
the standard interface for data access operations. All repositories
should inherit from this class to ensure consistent behavior.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Dict, Any
import asyncio
from dataclasses import dataclass
import logging

# Generic type variable for entity types
T = TypeVar('T')

logger = logging.getLogger(__name__)


@dataclass
class QueryFilter:
    """Represents a query filter with field, operator, and value."""
    field: str
    operator: str  # eq, ne, gt, lt, gte, lte, in, like
    value: Any


@dataclass
class QueryOptions:
    """Query options for listing operations."""
    limit: int = 100
    offset: int = 0
    order_by: Optional[str] = None
    order_desc: bool = False
    filters: Optional[List[QueryFilter]] = None


class BaseRepository(ABC, Generic[T]):
    """Abstract base repository providing CRUD operations.
    
    This repository follows the Repository pattern to abstract data access
    from business logic. It uses composition with DAO objects for actual
    data persistence operations.
    
    Type Parameters:
        T: Entity type this repository manages
    """

    @abstractmethod
    async def get(self, id: str) -> Optional[T]:
        """Get an entity by its ID.
        
        Args:
            id: Unique identifier for the entity
            
        Returns:
            Entity instance if found, None otherwise
            
        Raises:
            RepositoryError: If data access fails
        """
        pass

    @abstractmethod
    async def list(
        self, 
        options: Optional[QueryOptions] = None
    ) -> List[T]:
        """List entities with optional filtering and pagination.
        
        Args:
            options: Query options for filtering, sorting, and pagination
            
        Returns:
            List of entities matching the criteria
            
        Raises:
            RepositoryError: If data access fails
        """
        pass

    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create a new entity.
        
        Args:
            entity: Entity instance to create
            
        Returns:
            Created entity with generated ID and timestamps
            
        Raises:
            RepositoryError: If creation fails
            ValidationError: If entity data is invalid
        """
        pass

    @abstractmethod
    async def update(self, id: str, entity: T) -> Optional[T]:
        """Update an existing entity.
        
        Args:
            id: ID of entity to update
            entity: Updated entity data
            
        Returns:
            Updated entity if found and updated, None if not found
            
        Raises:
            RepositoryError: If update fails
            ValidationError: If entity data is invalid
        """
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete an entity by ID.
        
        Args:
            id: ID of entity to delete
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            RepositoryError: If deletion fails
        """
        pass

    async def exists(self, id: str) -> bool:
        """Check if an entity exists by ID.
        
        Args:
            id: ID to check
            
        Returns:
            True if entity exists, False otherwise
        """
        entity = await self.get(id)
        return entity is not None

    async def count(self, filters: Optional[List[QueryFilter]] = None) -> int:
        """Count entities matching filters.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            Count of entities matching criteria
            
        Raises:
            RepositoryError: If count operation fails
        """
        # Default implementation - subclasses can optimize this
        options = QueryOptions(limit=10000, filters=filters)
        entities = await self.list(options)
        return len(entities)

    async def bulk_create(self, entities: List[T]) -> List[T]:
        """Create multiple entities in bulk.
        
        Default implementation creates entities one by one.
        Subclasses can override for optimized bulk operations.
        
        Args:
            entities: List of entities to create
            
        Returns:
            List of created entities with IDs
            
        Raises:
            RepositoryError: If bulk creation fails
        """
        created_entities = []
        for entity in entities:
            created_entity = await self.create(entity)
            created_entities.append(created_entity)
        return created_entities

    async def bulk_delete(self, ids: List[str]) -> int:
        """Delete multiple entities by IDs.
        
        Default implementation deletes entities one by one.
        Subclasses can override for optimized bulk operations.
        
        Args:
            ids: List of IDs to delete
            
        Returns:
            Number of entities actually deleted
            
        Raises:
            RepositoryError: If bulk deletion fails
        """
        deleted_count = 0
        for entity_id in ids:
            was_deleted = await self.delete(entity_id)
            if was_deleted:
                deleted_count += 1
        return deleted_count


class RepositoryError(Exception):
    """Base exception for repository operations."""
    pass


class ValidationError(RepositoryError):
    """Raised when entity validation fails."""
    pass


class ConcurrencyError(RepositoryError):
    """Raised when concurrent access conflicts occur."""
    pass