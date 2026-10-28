"""User repository implementation with domain-specific operations.

This module implements the user repository following the Repository pattern.
It composes with UserDAO for data access and provides business-domain
specific methods like finding users by email or username.
"""

from typing import Optional, List
from datetime import datetime, timedelta
import logging

from models.entities.user.user import User
from dao.postgres.user_dao import UserDAO
from .base import BaseRepository, QueryOptions, QueryFilter, RepositoryError

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[User]):
    """Repository for User entity operations.
    
    Provides high-level business operations for users while delegating
    actual data persistence to the UserDAO. This separation allows for
    business logic to be independent of storage implementation details.
    """

    def __init__(self, dao: UserDAO) -> None:
        """Initialize repository with DAO dependency.
        
        Args:
            dao: UserDAO instance for data persistence
        """
        self.dao = dao

    async def get(self, id: str) -> Optional[User]:
        """Get user by ID.
        
        Args:
            id: User ID
            
        Returns:
            User instance if found, None otherwise
        """
        try:
            return await self.dao.find_by_id(id)
        except Exception as e:
            logger.error(f"Failed to get user {id}: {e}")
            raise RepositoryError(f"Failed to retrieve user: {e}") from e

    async def list(self, options: Optional[QueryOptions] = None) -> List[User]:
        """List users with optional filtering and pagination.
        
        Args:
            options: Query options for filtering and pagination
            
        Returns:
            List of users matching criteria
        """
        try:
            if options is None:
                options = QueryOptions()
            return await self.dao.find_many(
                limit=options.limit,
                offset=options.offset,
                order_by=options.order_by,
                order_desc=options.order_desc,
                filters=options.filters
            )
        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            raise RepositoryError(f"Failed to list users: {e}") from e

    async def create(self, user: User) -> User:
        """Create a new user.
        
        Args:
            user: User entity to create
            
        Returns:
            Created user with generated ID and timestamps
            
        Raises:
            RepositoryError: If creation fails
            ValidationError: If user data is invalid
        """
        try:
            # Validate user before creation
            await self._validate_user_for_creation(user)
            
            # Set creation timestamp
            user.created_at = datetime.utcnow()
            user.updated_at = user.created_at
            
            created_user = await self.dao.create(user)
            logger.info(f"Created user: {created_user.id}")
            return created_user
            
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise RepositoryError(f"Failed to create user: {e}") from e

    async def update(self, id: str, user: User) -> Optional[User]:
        """Update an existing user.
        
        Args:
            id: User ID to update
            user: Updated user data
            
        Returns:
            Updated user if found, None if not found
        """
        try:
            # Check if user exists
            existing_user = await self.dao.find_by_id(id)
            if existing_user is None:
                return None
                
            # Validate updated user data
            await self._validate_user_for_update(user, existing_user)
            
            # Set update timestamp
            user.updated_at = datetime.utcnow()
            
            updated_user = await self.dao.update(id, user)
            logger.info(f"Updated user: {id}")
            return updated_user
            
        except Exception as e:
            logger.error(f"Failed to update user {id}: {e}")
            raise RepositoryError(f"Failed to update user: {e}") from e

    async def delete(self, id: str) -> bool:
        """Delete a user by ID.
        
        Args:
            id: User ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        try:
            deleted = await self.dao.delete(id)
            if deleted:
                logger.info(f"Deleted user: {id}")
            return deleted
        except Exception as e:
            logger.error(f"Failed to delete user {id}: {e}")
            raise RepositoryError(f"Failed to delete user: {e}") from e

    # Domain-specific methods

    async def get_by_email(self, email: str) -> Optional[User]:
        """Find user by email address.
        
        Args:
            email: Email address to search for
            
        Returns:
            User if found, None otherwise
        """
        try:
            return await self.dao.find_by_email(email)
        except Exception as e:
            logger.error(f"Failed to find user by email {email}: {e}")
            raise RepositoryError(f"Failed to find user by email: {e}") from e

    async def get_by_username(self, username: str) -> Optional[User]:
        """Find user by username.
        
        Args:
            username: Username to search for
            
        Returns:
            User if found, None otherwise
        """
        try:
            return await self.dao.find_by_username(username)
        except Exception as e:
            logger.error(f"Failed to find user by username {username}: {e}")
            raise RepositoryError(f"Failed to find user by username: {e}") from e

    async def get_active_users(self, limit: int = 100) -> List[User]:
        """Get list of active users.
        
        Args:
            limit: Maximum number of users to return
            
        Returns:
            List of active users
        """
        try:
            filters = [QueryFilter(field="is_active", operator="eq", value=True)]
            options = QueryOptions(limit=limit, filters=filters)
            return await self.list(options)
        except Exception as e:
            logger.error(f"Failed to get active users: {e}")
            raise RepositoryError(f"Failed to get active users: {e}") from e

    async def get_users_created_since(self, since: datetime, limit: int = 100) -> List[User]:
        """Get users created since a specific date.
        
        Args:
            since: Datetime to filter from
            limit: Maximum number of users to return
            
        Returns:
            List of users created since the specified date
        """
        try:
            filters = [QueryFilter(field="created_at", operator="gte", value=since)]
            options = QueryOptions(
                limit=limit, 
                filters=filters,
                order_by="created_at",
                order_desc=True
            )
            return await self.list(options)
        except Exception as e:
            logger.error(f"Failed to get users created since {since}: {e}")
            raise RepositoryError(f"Failed to get users created since date: {e}") from e

    async def search_users(self, query: str, limit: int = 20) -> List[User]:
        """Search users by name or email.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            List of users matching the search query
        """
        try:
            return await self.dao.search(query, limit)
        except Exception as e:
            logger.error(f"Failed to search users with query '{query}': {e}")
            raise RepositoryError(f"Failed to search users: {e}") from e

    async def deactivate_user(self, id: str) -> Optional[User]:
        """Deactivate a user account.
        
        Args:
            id: User ID to deactivate
            
        Returns:
            Updated user if found, None if not found
        """
        try:
            user = await self.dao.find_by_id(id)
            if user is None:
                return None
                
            user.is_active = False
            user.deactivated_at = datetime.utcnow()
            
            updated_user = await self.dao.update(id, user)
            logger.info(f"Deactivated user: {id}")
            return updated_user
            
        except Exception as e:
            logger.error(f"Failed to deactivate user {id}: {e}")
            raise RepositoryError(f"Failed to deactivate user: {e}") from e

    async def activate_user(self, id: str) -> Optional[User]:
        """Activate a user account.
        
        Args:
            id: User ID to activate
            
        Returns:
            Updated user if found, None if not found
        """
        try:
            user = await self.dao.find_by_id(id)
            if user is None:
                return None
                
            user.is_active = True
            user.deactivated_at = None
            
            updated_user = await self.dao.update(id, user)
            logger.info(f"Activated user: {id}")
            return updated_user
            
        except Exception as e:
            logger.error(f"Failed to activate user {id}: {e}")
            raise RepositoryError(f"Failed to activate user: {e}") from e

    # Private validation methods

    async def _validate_user_for_creation(self, user: User) -> None:
        """Validate user data for creation.
        
        Args:
            user: User entity to validate
            
        Raises:
            ValidationError: If validation fails
        """
        from .base import ValidationError
        
        # Check for required fields
        if not user.email:
            raise ValidationError("Email is required")
        if not user.username:
            raise ValidationError("Username is required")
            
        # Check for uniqueness
        existing_email = await self.get_by_email(user.email)
        if existing_email:
            raise ValidationError(f"Email {user.email} is already taken")
            
        existing_username = await self.get_by_username(user.username)
        if existing_username:
            raise ValidationError(f"Username {user.username} is already taken")

    async def _validate_user_for_update(self, user: User, existing_user: User) -> None:
        """Validate user data for update.
        
        Args:
            user: Updated user data
            existing_user: Current user data
            
        Raises:
            ValidationError: If validation fails
        """
        from .base import ValidationError
        
        # Check email uniqueness if changed
        if user.email and user.email != existing_user.email:
            existing_email = await self.get_by_email(user.email)
            if existing_email and existing_email.id != existing_user.id:
                raise ValidationError(f"Email {user.email} is already taken")
                
        # Check username uniqueness if changed
        if user.username and user.username != existing_user.username:
            existing_username = await self.get_by_username(user.username)
            if existing_username and existing_username.id != existing_user.id:
                raise ValidationError(f"Username {user.username} is already taken")