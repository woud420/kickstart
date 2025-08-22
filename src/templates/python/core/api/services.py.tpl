"""Business logic services for {{service_name}}.

Services contain the business logic and use cases for the application.
They coordinate between repositories and enforce business rules.
"""

from typing import List, Optional
from datetime import datetime

from ..model.entities import User, UserProfile
from ..model.dto import (
    CreateUserRequest, UpdateUserRequest, UserResponse, UserListResponse,
    CreateUserProfileRequest, UpdateUserProfileRequest, UserProfileResponse,
    PaginationRequest
)
from ..model.repository import (
    UserRepository, UserProfileRepository,
    UserNotFoundError, UserAlreadyExistsError,
    ProfileNotFoundError, ProfileAlreadyExistsError
)


class UserService:
    """Service for user-related business logic."""
    
    def __init__(self, user_repo: UserRepository, profile_repo: UserProfileRepository):
        """Initialize the user service.
        
        Args:
            user_repo: User repository instance
            profile_repo: User profile repository instance
        """
        self.user_repo = user_repo
        self.profile_repo = profile_repo
    
    async def create_user(self, request: CreateUserRequest) -> UserResponse:
        """Create a new user.
        
        Args:
            request: User creation request
            
        Returns:
            Created user response
            
        Raises:
            UserAlreadyExistsError: If user already exists
            ValidationError: If request data is invalid
        """
        # Check if user already exists
        if await self.user_repo.exists_by_username(request.username):
            raise UserAlreadyExistsError(f"User with username '{request.username}' already exists")
        
        if await self.user_repo.exists_by_email(request.email):
            raise UserAlreadyExistsError(f"User with email '{request.email}' already exists")
        
        # Create user entity
        user = User(
            username=request.username,
            email=request.email,
            full_name=request.full_name,
            profile_data=request.profile_data
        )
        
        # Save user
        created_user = await self.user_repo.create(user)
        
        return UserResponse.from_entity(created_user)
    
    async def get_user(self, user_id: str) -> UserResponse:
        """Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User response
            
        Raises:
            UserNotFoundError: If user not found
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID '{user_id}' not found")
        
        return UserResponse.from_entity(user)
    
    async def get_user_by_username(self, username: str) -> UserResponse:
        """Get user by username.
        
        Args:
            username: Username
            
        Returns:
            User response
            
        Raises:
            UserNotFoundError: If user not found
        """
        user = await self.user_repo.get_by_username(username)
        if not user:
            raise UserNotFoundError(f"User with username '{username}' not found")
        
        return UserResponse.from_entity(user)
    
    async def list_users(self, pagination: PaginationRequest) -> UserListResponse:
        """List users with pagination.
        
        Args:
            pagination: Pagination parameters
            
        Returns:
            Paginated user list response
        """
        users, total = await self.user_repo.list_users(pagination)
        
        return UserListResponse.from_entities(
            users=users,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size
        )
    
    async def update_user(self, user_id: str, request: UpdateUserRequest) -> UserResponse:
        """Update user.
        
        Args:
            user_id: User ID
            request: Update request
            
        Returns:
            Updated user response
            
        Raises:
            UserNotFoundError: If user not found
            ValidationError: If request data is invalid
        """
        if not request.has_updates():
            raise ValueError("No updates provided")
        
        # Get existing user
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID '{user_id}' not found")
        
        # Apply updates
        if request.full_name is not None:
            user.full_name = request.full_name
        
        if request.profile_data is not None:
            user.update_profile(request.profile_data)
        
        user.updated_at = datetime.utcnow()
        
        # Save updates
        updated_user = await self.user_repo.update(user)
        
        return UserResponse.from_entity(updated_user)
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted successfully
            
        Raises:
            UserNotFoundError: If user not found
        """
        # Check if user exists
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID '{user_id}' not found")
        
        # Delete user profile if exists
        await self.profile_repo.delete(user_id)
        
        # Delete user
        return await self.user_repo.delete(user_id)
    
    async def activate_user(self, user_id: str) -> UserResponse:
        """Activate user.
        
        Args:
            user_id: User ID
            
        Returns:
            Updated user response
            
        Raises:
            UserNotFoundError: If user not found
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID '{user_id}' not found")
        
        user.activate()
        updated_user = await self.user_repo.update(user)
        
        return UserResponse.from_entity(updated_user)
    
    async def deactivate_user(self, user_id: str) -> UserResponse:
        """Deactivate user.
        
        Args:
            user_id: User ID
            
        Returns:
            Updated user response
            
        Raises:
            UserNotFoundError: If user not found
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID '{user_id}' not found")
        
        user.deactivate()
        updated_user = await self.user_repo.update(user)
        
        return UserResponse.from_entity(updated_user)


class UserProfileService:
    """Service for user profile-related business logic."""
    
    def __init__(self, user_repo: UserRepository, profile_repo: UserProfileRepository):
        """Initialize the user profile service.
        
        Args:
            user_repo: User repository instance
            profile_repo: User profile repository instance
        """
        self.user_repo = user_repo
        self.profile_repo = profile_repo
    
    async def create_profile(self, user_id: str, request: CreateUserProfileRequest) -> UserProfileResponse:
        """Create user profile.
        
        Args:
            user_id: User ID
            request: Profile creation request
            
        Returns:
            Created profile response
            
        Raises:
            UserNotFoundError: If user not found
            ProfileAlreadyExistsError: If profile already exists
        """
        # Check if user exists
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID '{user_id}' not found")
        
        # Check if profile already exists
        existing_profile = await self.profile_repo.get_by_user_id(user_id)
        if existing_profile:
            raise ProfileAlreadyExistsError(f"Profile for user '{user_id}' already exists")
        
        # Create profile entity
        profile = UserProfile(
            user_id=user_id,
            bio=request.bio,
            avatar_url=request.avatar_url,
            location=request.location,
            website=request.website,
            social_links=request.social_links,
            preferences=request.preferences
        )
        
        # Save profile
        created_profile = await self.profile_repo.create(profile)
        
        return UserProfileResponse.from_entity(created_profile)
    
    async def get_profile(self, user_id: str) -> UserProfileResponse:
        """Get user profile.
        
        Args:
            user_id: User ID
            
        Returns:
            Profile response
            
        Raises:
            ProfileNotFoundError: If profile not found
        """
        profile = await self.profile_repo.get_by_user_id(user_id)
        if not profile:
            raise ProfileNotFoundError(f"Profile for user '{user_id}' not found")
        
        return UserProfileResponse.from_entity(profile)
    
    async def update_profile(self, user_id: str, request: UpdateUserProfileRequest) -> UserProfileResponse:
        """Update user profile.
        
        Args:
            user_id: User ID
            request: Update request
            
        Returns:
            Updated profile response
            
        Raises:
            ProfileNotFoundError: If profile not found
            ValidationError: If request data is invalid
        """
        if not request.has_updates():
            raise ValueError("No updates provided")
        
        # Get existing profile
        profile = await self.profile_repo.get_by_user_id(user_id)
        if not profile:
            raise ProfileNotFoundError(f"Profile for user '{user_id}' not found")
        
        # Apply updates
        if request.bio is not None:
            profile.bio = request.bio
        
        if request.avatar_url is not None:
            profile.avatar_url = request.avatar_url
        
        if request.location is not None:
            profile.location = request.location
        
        if request.website is not None:
            profile.website = request.website
        
        if request.social_links is not None:
            profile.update_social_links(request.social_links)
        
        if request.preferences is not None:
            profile.update_preferences(request.preferences)
        
        profile.updated_at = datetime.utcnow()
        
        # Save updates
        updated_profile = await self.profile_repo.update(profile)
        
        return UserProfileResponse.from_entity(updated_profile)
    
    async def delete_profile(self, user_id: str) -> bool:
        """Delete user profile.
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted successfully
            
        Raises:
            ProfileNotFoundError: If profile not found
        """
        # Check if profile exists
        profile = await self.profile_repo.get_by_user_id(user_id)
        if not profile:
            raise ProfileNotFoundError(f"Profile for user '{user_id}' not found")
        
        # Delete profile
        return await self.profile_repo.delete(user_id)