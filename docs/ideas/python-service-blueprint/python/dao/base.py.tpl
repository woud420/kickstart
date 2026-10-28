"""Base Data Access Object (DAO) for database operations.

This module provides the abstract base DAO class that defines the interface
for database-specific operations. DAOs handle the actual database interactions
and SQL execution while repositories provide business-domain abstractions.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Dict, Any, Union
import asyncio
import logging
from contextlib import asynccontextmanager

# Generic type variable for entity types
T = TypeVar('T')

logger = logging.getLogger(__name__)


class BaseDAO(ABC, Generic[T]):
    """Abstract base Data Access Object.
    
    DAOs are responsible for:
    - Database connection management
    - SQL query execution
    - Result set mapping to entities
    - Transaction handling
    - Database-specific optimizations
    
    Type Parameters:
        T: Entity type this DAO manages
    """

    def __init__(self, connection_pool: Any) -> None:
        """Initialize DAO with database connection pool.
        
        Args:
            connection_pool: Database connection pool (asyncpg, psycopg3, etc.)
        """
        self.pool = connection_pool

    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[T]:
        """Find entity by ID.
        
        Args:
            id: Entity ID
            
        Returns:
            Entity if found, None otherwise
            
        Raises:
            DatabaseError: If query execution fails
        """
        pass

    @abstractmethod
    async def find_many(
        self,
        limit: int = 100,
        offset: int = 0,
        order_by: Optional[str] = None,
        order_desc: bool = False,
        filters: Optional[List[Any]] = None
    ) -> List[T]:
        """Find multiple entities with filtering and pagination.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            order_by: Field to order by
            order_desc: Whether to order descending
            filters: List of filter conditions
            
        Returns:
            List of entities matching criteria
            
        Raises:
            DatabaseError: If query execution fails
        """
        pass

    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create a new entity.
        
        Args:
            entity: Entity to create
            
        Returns:
            Created entity with generated fields
            
        Raises:
            DatabaseError: If creation fails
        """
        pass

    @abstractmethod
    async def update(self, id: str, entity: T) -> Optional[T]:
        """Update an existing entity.
        
        Args:
            id: Entity ID
            entity: Updated entity data
            
        Returns:
            Updated entity if found, None otherwise
            
        Raises:
            DatabaseError: If update fails
        """
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete an entity by ID.
        
        Args:
            id: Entity ID
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            DatabaseError: If deletion fails
        """
        pass

    async def count(self, filters: Optional[List[Any]] = None) -> int:
        """Count entities matching filters.
        
        Args:
            filters: Optional filter conditions
            
        Returns:
            Count of matching entities
            
        Raises:
            DatabaseError: If count query fails
        """
        # Base implementation - subclasses should override for efficiency
        entities = await self.find_many(limit=10000, filters=filters)
        return len(entities)

    async def exists(self, id: str) -> bool:
        """Check if entity exists by ID.
        
        Args:
            id: Entity ID to check
            
        Returns:
            True if entity exists, False otherwise
        """
        entity = await self.find_by_id(id)
        return entity is not None

    @asynccontextmanager
    async def transaction(self):
        """Database transaction context manager.
        
        Usage:
            async with dao.transaction() as tx:
                await dao.create(entity1, connection=tx)
                await dao.create(entity2, connection=tx)
                # Transaction committed automatically
        
        Yields:
            Database connection/transaction object
            
        Raises:
            DatabaseError: If transaction fails
        """
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                try:
                    yield connection
                except Exception as e:
                    logger.error(f"Transaction failed: {e}")
                    raise

    def _build_where_clause(
        self,
        filters: Optional[List[Any]] = None,
        params: Optional[List[Any]] = None
    ) -> tuple[str, List[Any]]:
        """Build SQL WHERE clause from filters.
        
        Args:
            filters: List of filter objects
            params: List to append parameters to
            
        Returns:
            Tuple of (where_clause, parameters)
        """
        if not filters:
            return "", params or []
            
        if params is None:
            params = []
            
        conditions = []
        
        for filter_obj in filters:
            if hasattr(filter_obj, 'field') and hasattr(filter_obj, 'operator') and hasattr(filter_obj, 'value'):
                condition, new_params = self._build_filter_condition(filter_obj, len(params) + 1)
                conditions.append(condition)
                params.extend(new_params)
        
        if conditions:
            return f"WHERE {' AND '.join(conditions)}", params
        return "", params

    def _build_filter_condition(self, filter_obj: Any, param_start: int) -> tuple[str, List[Any]]:
        """Build a single filter condition.
        
        Args:
            filter_obj: Filter object with field, operator, value
            param_start: Starting parameter number for this condition
            
        Returns:
            Tuple of (condition_sql, parameters)
        """
        field = filter_obj.field
        operator = filter_obj.operator.lower()
        value = filter_obj.value
        
        if operator == "eq":
            return f"{field} = ${param_start}", [value]
        elif operator == "ne":
            return f"{field} != ${param_start}", [value]
        elif operator == "gt":
            return f"{field} > ${param_start}", [value]
        elif operator == "lt":
            return f"{field} < ${param_start}", [value]
        elif operator == "gte":
            return f"{field} >= ${param_start}", [value]
        elif operator == "lte":
            return f"{field} <= ${param_start}", [value]
        elif operator == "like":
            return f"{field} LIKE ${param_start}", [f"%{value}%"]
        elif operator == "in":
            if not isinstance(value, (list, tuple)):
                value = [value]
            placeholders = ", ".join([f"${param_start + i}" for i in range(len(value))])
            return f"{field} IN ({placeholders})", list(value)
        else:
            raise ValueError(f"Unsupported filter operator: {operator}")

    def _build_order_clause(self, order_by: Optional[str] = None, order_desc: bool = False) -> str:
        """Build SQL ORDER BY clause.
        
        Args:
            order_by: Field to order by
            order_desc: Whether to order descending
            
        Returns:
            ORDER BY clause string
        """
        if not order_by:
            return ""
        
        direction = "DESC" if order_desc else "ASC"
        return f"ORDER BY {order_by} {direction}"

    async def bulk_create(self, entities: List[T]) -> List[T]:
        """Create multiple entities in a single operation.
        
        Default implementation creates entities one by one in a transaction.
        Subclasses can override for database-specific bulk operations.
        
        Args:
            entities: List of entities to create
            
        Returns:
            List of created entities with generated fields
            
        Raises:
            DatabaseError: If bulk creation fails
        """
        async with self.transaction() as tx:
            created_entities = []
            for entity in entities:
                created_entity = await self.create(entity)
                created_entities.append(created_entity)
            return created_entities

    async def bulk_delete(self, ids: List[str]) -> int:
        """Delete multiple entities by IDs.
        
        Default implementation deletes entities one by one in a transaction.
        Subclasses can override for database-specific bulk operations.
        
        Args:
            ids: List of entity IDs to delete
            
        Returns:
            Number of entities actually deleted
            
        Raises:
            DatabaseError: If bulk deletion fails
        """
        async with self.transaction() as tx:
            deleted_count = 0
            for entity_id in ids:
                was_deleted = await self.delete(entity_id)
                if was_deleted:
                    deleted_count += 1
            return deleted_count


class DatabaseError(Exception):
    """Base exception for database operations."""
    pass


class ConnectionError(DatabaseError):
    """Raised when database connection fails."""
    pass


class QueryError(DatabaseError):
    """Raised when SQL query execution fails."""
    pass


class IntegrityError(DatabaseError):
    """Raised when database integrity constraints are violated."""
    pass