"""Repository interfaces for data access.

Repository pattern provides a unified interface for data access operations,
abstracting the underlying data storage implementation.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from .entities import User, UserProfile
from .dto import PaginationRequest


class UserRepository(ABC):
    """Abstract repository interface for User operations."""
    
    @abstractmethod
    async def create(self, user: User) -> User:
        """Create a new user.
        
        Args:
            user: User entity to create
            
        Returns:
            Created user entity
            
        Raises:
            RepositoryError: If creation fails
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID.
        
        Args:
            user_id: User ID to search for
            
        Returns:
            User entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username.
        
        Args:
            username: Username to search for
            
        Returns:
            User entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email.
        
        Args:
            email: Email to search for
            
        Returns:
            User entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def list_users(self, pagination: PaginationRequest) -> tuple[List[User], int]:
        """List users with pagination.
        
        Args:
            pagination: Pagination parameters
            
        Returns:
            Tuple of (users list, total count)
        """
        pass
    
    @abstractmethod
    async def update(self, user: User) -> User:
        """Update an existing user.
        
        Args:
            user: User entity with updated data
            
        Returns:
            Updated user entity
            
        Raises:
            RepositoryError: If update fails
        """
        pass
    
    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """Delete a user.
        
        Args:
            user_id: ID of user to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def exists_by_username(self, username: str) -> bool:
        """Check if user exists by username.
        
        Args:
            username: Username to check
            
        Returns:
            True if user exists, False otherwise
        """
        pass
    
    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email.
        
        Args:
            email: Email to check
            
        Returns:
            True if user exists, False otherwise
        """
        pass


class UserProfileRepository(ABC):
    """Abstract repository interface for UserProfile operations."""
    
    @abstractmethod
    async def create(self, profile: UserProfile) -> UserProfile:
        """Create a new user profile.
        
        Args:
            profile: UserProfile entity to create
            
        Returns:
            Created profile entity
            
        Raises:
            RepositoryError: If creation fails
        """
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: str) -> Optional[UserProfile]:
        """Get profile by user ID.
        
        Args:
            user_id: User ID to search for
            
        Returns:
            UserProfile entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def update(self, profile: UserProfile) -> UserProfile:
        """Update an existing profile.
        
        Args:
            profile: UserProfile entity with updated data
            
        Returns:
            Updated profile entity
            
        Raises:
            RepositoryError: If update fails
        """
        pass
    
    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """Delete a user profile.
        
        Args:
            user_id: User ID whose profile to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        pass


# In-memory implementations for core functionality
class InMemoryUserRepository(UserRepository):
    """In-memory implementation of UserRepository for core functionality."""
    
    def __init__(self):
        """Initialize the in-memory repository."""
        self._users: Dict[str, User] = {}
        self._username_index: Dict[str, str] = {}
        self._email_index: Dict[str, str] = {}
    
    async def create(self, user: User) -> User:
        """Create a new user in memory."""
        if user.id in self._users:
            raise ValueError(f"User with ID {user.id} already exists")
        if user.username in self._username_index:
            raise ValueError(f"User with username {user.username} already exists")
        if user.email in self._email_index:
            raise ValueError(f"User with email {user.email} already exists")
        
        self._users[user.id] = user
        self._username_index[user.username] = user.id
        self._email_index[user.email] = user.id
        
        return user
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID from memory."""
        return self._users.get(user_id)
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username from memory."""
        user_id = self._username_index.get(username)
        return self._users.get(user_id) if user_id else None
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email from memory."""
        user_id = self._email_index.get(email)
        return self._users.get(user_id) if user_id else None
    
    async def list_users(self, pagination: PaginationRequest) -> tuple[List[User], int]:
        """List users with pagination from memory."""
        all_users = list(self._users.values())
        
        # Simple sorting by created_at
        if pagination.sort_by == "created_at":
            all_users.sort(
                key=lambda u: u.created_at,
                reverse=(pagination.sort_order == "desc")
            )
        elif pagination.sort_by == "username":
            all_users.sort(
                key=lambda u: u.username,
                reverse=(pagination.sort_order == "desc")
            )
        
        # Apply pagination
        start_idx = pagination.offset
        end_idx = start_idx + pagination.page_size
        paginated_users = all_users[start_idx:end_idx]
        
        return paginated_users, len(all_users)
    
    async def update(self, user: User) -> User:
        """Update user in memory."""
        if user.id not in self._users:
            raise ValueError(f"User with ID {user.id} not found")
        
        old_user = self._users[user.id]
        
        # Update indexes if username or email changed
        if old_user.username != user.username:
            if user.username in self._username_index:
                raise ValueError(f"User with username {user.username} already exists")
            del self._username_index[old_user.username]
            self._username_index[user.username] = user.id
        
        if old_user.email != user.email:
            if user.email in self._email_index:
                raise ValueError(f"User with email {user.email} already exists")
            del self._email_index[old_user.email]
            self._email_index[user.email] = user.id
        
        self._users[user.id] = user
        return user
    
    async def delete(self, user_id: str) -> bool:
        """Delete user from memory."""
        user = self._users.get(user_id)
        if not user:
            return False
        
        del self._users[user_id]
        del self._username_index[user.username]
        del self._email_index[user.email]
        
        return True
    
    async def exists_by_username(self, username: str) -> bool:
        """Check if user exists by username in memory."""
        return username in self._username_index
    
    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email in memory."""
        return email in self._email_index


class InMemoryUserProfileRepository(UserProfileRepository):
    """In-memory implementation of UserProfileRepository for core functionality."""
    
    def __init__(self):
        """Initialize the in-memory repository."""
        self._profiles: Dict[str, UserProfile] = {}
    
    async def create(self, profile: UserProfile) -> UserProfile:
        """Create a new profile in memory."""
        if profile.user_id in self._profiles:
            raise ValueError(f"Profile for user {profile.user_id} already exists")
        
        self._profiles[profile.user_id] = profile
        return profile
    
    async def get_by_user_id(self, user_id: str) -> Optional[UserProfile]:
        """Get profile by user ID from memory."""
        return self._profiles.get(user_id)
    
    async def update(self, profile: UserProfile) -> UserProfile:
        """Update profile in memory."""
        if profile.user_id not in self._profiles:
            raise ValueError(f"Profile for user {profile.user_id} not found")
        
        self._profiles[profile.user_id] = profile
        return profile
    
    async def delete(self, user_id: str) -> bool:
        """Delete profile from memory."""
        if user_id in self._profiles:
            del self._profiles[user_id]
            return True
        return False


# Repository exceptions
class RepositoryError(Exception):
    """Base exception for repository operations."""
    pass


class UserNotFoundError(RepositoryError):
    """Exception raised when user is not found."""
    pass


class UserAlreadyExistsError(RepositoryError):
    """Exception raised when user already exists."""
    pass


class ProfileNotFoundError(RepositoryError):
    """Exception raised when profile is not found."""
    pass


class ProfileAlreadyExistsError(RepositoryError):
    """Exception raised when profile already exists."""
    pass