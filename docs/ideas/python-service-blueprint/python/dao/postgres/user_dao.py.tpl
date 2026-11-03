"""PostgreSQL implementation of UserDAO.

This module provides PostgreSQL-specific data access operations for User entities.
It uses asyncpg for high-performance async database operations and implements
the DAO interface defined in the base module.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import asyncpg
import uuid

from models.entities.user.user import User
from dao.base import BaseDAO, DatabaseError, QueryError, IntegrityError

logger = logging.getLogger(__name__)


class UserDAO(BaseDAO[User]):
    """PostgreSQL Data Access Object for User entities.
    
    Implements CRUD operations and user-specific queries using asyncpg.
    Handles connection pooling, error mapping, and SQL query execution.
    """

    def __init__(self, connection_pool: asyncpg.Pool) -> None:
        """Initialize UserDAO with asyncpg connection pool.
        
        Args:
            connection_pool: asyncpg connection pool
        """
        super().__init__(connection_pool)
        self.pool: asyncpg.Pool = connection_pool

    async def find_by_id(self, id: str) -> Optional[User]:
        """Find user by ID.
        
        Args:
            id: User ID
            
        Returns:
            User if found, None otherwise
            
        Raises:
            DatabaseError: If query execution fails
        """
        query = """
            SELECT id, username, email, full_name, is_active, 
                   created_at, updated_at, last_login_at, deactivated_at,
                   password_hash, profile_data
            FROM users 
            WHERE id = $1
        """
        
        try:
            async with self.pool.acquire() as connection:
                row = await connection.fetchrow(query, id)
                if row:
                    return self._row_to_user(row)
                return None
        except asyncpg.PostgresError as e:
            logger.error(f"Failed to find user by ID {id}: {e}")
            raise DatabaseError(f"Database query failed: {e}") from e

    async def find_many(
        self,
        limit: int = 100,
        offset: int = 0,
        order_by: Optional[str] = None,
        order_desc: bool = False,
        filters: Optional[List[Any]] = None
    ) -> List[User]:
        """Find multiple users with filtering and pagination.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            order_by: Field to order by
            order_desc: Whether to order descending
            filters: List of filter conditions
            
        Returns:
            List of users matching criteria
        """
        base_query = """
            SELECT id, username, email, full_name, is_active,
                   created_at, updated_at, last_login_at, deactivated_at,
                   password_hash, profile_data
            FROM users
        """
        
        params = []
        where_clause, params = self._build_where_clause(filters, params)
        order_clause = self._build_order_clause(order_by or "created_at", order_desc)
        
        query = f"""
            {base_query}
            {where_clause}
            {order_clause}
            LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}
        """
        params.extend([limit, offset])
        
        try:
            async with self.pool.acquire() as connection:
                rows = await connection.fetch(query, *params)
                return [self._row_to_user(row) for row in rows]
        except asyncpg.PostgresError as e:
            logger.error(f"Failed to find users: {e}")
            raise DatabaseError(f"Database query failed: {e}") from e

    async def create(self, user: User) -> User:
        """Create a new user.
        
        Args:
            user: User entity to create
            
        Returns:
            Created user with generated ID and timestamps
            
        Raises:
            DatabaseError: If creation fails
            IntegrityError: If unique constraints are violated
        """
        # Generate ID if not provided
        if not user.id:
            user.id = str(uuid.uuid4())
            
        # Set timestamps
        now = datetime.utcnow()
        user.created_at = now
        user.updated_at = now
        
        query = """
            INSERT INTO users (
                id, username, email, full_name, is_active,
                created_at, updated_at, last_login_at, deactivated_at,
                password_hash, profile_data
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING id, username, email, full_name, is_active,
                      created_at, updated_at, last_login_at, deactivated_at,
                      password_hash, profile_data
        """
        
        try:
            async with self.pool.acquire() as connection:
                row = await connection.fetchrow(
                    query,
                    user.id,
                    user.username,
                    user.email,
                    user.full_name,
                    user.is_active,
                    user.created_at,
                    user.updated_at,
                    user.last_login_at,
                    user.deactivated_at,
                    user.password_hash,
                    user.profile_data
                )
                logger.info(f"Created user: {user.id}")
                return self._row_to_user(row)
                
        except asyncpg.UniqueViolationError as e:
            logger.warning(f"Unique constraint violation creating user: {e}")
            raise IntegrityError(f"User with this email or username already exists") from e
        except asyncpg.PostgresError as e:
            logger.error(f"Failed to create user: {e}")
            raise DatabaseError(f"Database query failed: {e}") from e

    async def update(self, id: str, user: User) -> Optional[User]:
        """Update an existing user.
        
        Args:
            id: User ID to update
            user: Updated user data
            
        Returns:
            Updated user if found, None if not found
            
        Raises:
            DatabaseError: If update fails
            IntegrityError: If unique constraints are violated
        """
        # Set update timestamp
        user.updated_at = datetime.utcnow()
        
        query = """
            UPDATE users SET
                username = $2,
                email = $3,
                full_name = $4,
                is_active = $5,
                updated_at = $6,
                last_login_at = $7,
                deactivated_at = $8,
                password_hash = $9,
                profile_data = $10
            WHERE id = $1
            RETURNING id, username, email, full_name, is_active,
                      created_at, updated_at, last_login_at, deactivated_at,
                      password_hash, profile_data
        """
        
        try:
            async with self.pool.acquire() as connection:
                row = await connection.fetchrow(
                    query,
                    id,
                    user.username,
                    user.email,
                    user.full_name,
                    user.is_active,
                    user.updated_at,
                    user.last_login_at,
                    user.deactivated_at,
                    user.password_hash,
                    user.profile_data
                )
                if row:
                    logger.info(f"Updated user: {id}")
                    return self._row_to_user(row)
                return None
                
        except asyncpg.UniqueViolationError as e:
            logger.warning(f"Unique constraint violation updating user {id}: {e}")
            raise IntegrityError(f"User with this email or username already exists") from e
        except asyncpg.PostgresError as e:
            logger.error(f"Failed to update user {id}: {e}")
            raise DatabaseError(f"Database query failed: {e}") from e

    async def delete(self, id: str) -> bool:
        """Delete a user by ID.
        
        Args:
            id: User ID to delete
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            DatabaseError: If deletion fails
        """
        query = "DELETE FROM users WHERE id = $1"
        
        try:
            async with self.pool.acquire() as connection:
                result = await connection.execute(query, id)
                deleted = result == "DELETE 1"
                if deleted:
                    logger.info(f"Deleted user: {id}")
                return deleted
        except asyncpg.PostgresError as e:
            logger.error(f"Failed to delete user {id}: {e}")
            raise DatabaseError(f"Database query failed: {e}") from e

    async def count(self, filters: Optional[List[Any]] = None) -> int:
        """Count users matching filters.
        
        Args:
            filters: Optional filter conditions
            
        Returns:
            Count of matching users
        """
        base_query = "SELECT COUNT(*) FROM users"
        
        params = []
        where_clause, params = self._build_where_clause(filters, params)
        query = f"{base_query} {where_clause}"
        
        try:
            async with self.pool.acquire() as connection:
                count = await connection.fetchval(query, *params)
                return count
        except asyncpg.PostgresError as e:
            logger.error(f"Failed to count users: {e}")
            raise DatabaseError(f"Database query failed: {e}") from e

    # User-specific query methods

    async def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email address.
        
        Args:
            email: Email address
            
        Returns:
            User if found, None otherwise
        """
        query = """
            SELECT id, username, email, full_name, is_active,
                   created_at, updated_at, last_login_at, deactivated_at,
                   password_hash, profile_data
            FROM users 
            WHERE email = $1
        """
        
        try:
            async with self.pool.acquire() as connection:
                row = await connection.fetchrow(query, email)
                if row:
                    return self._row_to_user(row)
                return None
        except asyncpg.PostgresError as e:
            logger.error(f"Failed to find user by email {email}: {e}")
            raise DatabaseError(f"Database query failed: {e}") from e

    async def find_by_username(self, username: str) -> Optional[User]:
        """Find user by username.
        
        Args:
            username: Username
            
        Returns:
            User if found, None otherwise
        """
        query = """
            SELECT id, username, email, full_name, is_active,
                   created_at, updated_at, last_login_at, deactivated_at,
                   password_hash, profile_data
            FROM users 
            WHERE username = $1
        """
        
        try:
            async with self.pool.acquire() as connection:
                row = await connection.fetchrow(query, username)
                if row:
                    return self._row_to_user(row)
                return None
        except asyncpg.PostgresError as e:
            logger.error(f"Failed to find user by username {username}: {e}")
            raise DatabaseError(f"Database query failed: {e}") from e

    async def search(self, query_text: str, limit: int = 20) -> List[User]:
        """Search users by name or email.
        
        Args:
            query_text: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching users
        """
        query = """
            SELECT id, username, email, full_name, is_active,
                   created_at, updated_at, last_login_at, deactivated_at,
                   password_hash, profile_data
            FROM users 
            WHERE full_name ILIKE $1 OR email ILIKE $1 OR username ILIKE $1
            ORDER BY 
                CASE 
                    WHEN username ILIKE $1 THEN 1
                    WHEN email ILIKE $1 THEN 2
                    ELSE 3
                END,
                full_name
            LIMIT $2
        """
        
        search_pattern = f"%{query_text}%"
        
        try:
            async with self.pool.acquire() as connection:
                rows = await connection.fetch(query, search_pattern, limit)
                return [self._row_to_user(row) for row in rows]
        except asyncpg.PostgresError as e:
            logger.error(f"Failed to search users: {e}")
            raise DatabaseError(f"Database query failed: {e}") from e

    async def update_last_login(self, id: str) -> bool:
        """Update user's last login timestamp.
        
        Args:
            id: User ID
            
        Returns:
            True if updated, False if user not found
        """
        query = """
            UPDATE users 
            SET last_login_at = $2, updated_at = $2
            WHERE id = $1
        """
        
        now = datetime.utcnow()
        
        try:
            async with self.pool.acquire() as connection:
                result = await connection.execute(query, id, now)
                updated = result == "UPDATE 1"
                if updated:
                    logger.info(f"Updated last login for user: {id}")
                return updated
        except asyncpg.PostgresError as e:
            logger.error(f"Failed to update last login for user {id}: {e}")
            raise DatabaseError(f"Database query failed: {e}") from e

    def _row_to_user(self, row: asyncpg.Record) -> User:
        """Convert database row to User entity.
        
        Args:
            row: Database row record
            
        Returns:
            User entity
        """
        return User(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            full_name=row['full_name'],
            is_active=row['is_active'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            last_login_at=row['last_login_at'],
            deactivated_at=row['deactivated_at'],
            password_hash=row['password_hash'],
            profile_data=row['profile_data']
        )