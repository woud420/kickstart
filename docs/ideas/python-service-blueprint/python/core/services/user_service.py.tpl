"""User service for business logic operations.

This module implements the UserService class that handles all business
logic related to user management. It coordinates between repositories,
validates business rules, and manages user-related operations.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import hashlib
import secrets

from models.entities.user.user import User
from models.dto.requests import CreateUserRequest, UpdateUserRequest
from models.dto.responses import UserResponse, UserListResponse
from repository.user_repo import UserRepository
from .base_service import BaseService
from .exceptions import (
    ValidationError,
    NotFoundError,
    ConflictError,
    BusinessRuleError
)

logger = logging.getLogger(__name__)


class UserService(BaseService):
    """Business service for user management operations.
    
    Handles user creation, updates, authentication, and other user-related
    business logic. Uses dependency injection to receive repositories and
    external services needed for operations.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        email_service: Optional[Any] = None,
        notification_service: Optional[Any] = None
    ) -> None:
        """Initialize UserService with dependencies.
        
        Args:
            user_repository: Repository for user data operations
            email_service: Optional email service for notifications
            notification_service: Optional notification service
        """
        super().__init__()
        self.user_repository = user_repository
        self.email_service = email_service
        self.notification_service = notification_service

    async def create_user(self, request: CreateUserRequest) -> UserResponse:
        """Create a new user account.
        
        Args:
            request: User creation request data
            
        Returns:
            Created user response
            
        Raises:
            ValidationError: If user data is invalid
            ConflictError: If email or username already exists
        """
        try:
            self._log_operation("create_user", context={"email": request.email})
            
            # Validate request data
            await self._validate_create_user_request(request)
            
            # Create user entity from request
            user = User(
                username=request.username,
                email=request.email,
                full_name=request.full_name,
                password_hash=self._hash_password(request.password),
                is_active=True,
                profile_data=request.profile_data or {}
            )
            
            # Create user in repository
            created_user = await self.user_repository.create(user)
            
            # Send welcome email if email service is available
            if self.email_service:
                await self._send_welcome_email(created_user)
            
            self._log_operation("create_user_success", created_user.id)
            return UserResponse.from_entity(created_user)
            
        except Exception as e:
            self._handle_service_error(e, "create_user")

    async def get_user(self, user_id: str) -> UserResponse:
        """Get user by ID.
        
        Args:
            user_id: User ID to retrieve
            
        Returns:
            User response data
            
        Raises:
            NotFoundError: If user not found
        """
        try:
            self._log_operation("get_user", user_id)
            
            user = await self.user_repository.get(user_id)
            if not user:
                raise NotFoundError(f"User not found: {user_id}")
                
            return UserResponse.from_entity(user)
            
        except Exception as e:
            self._handle_service_error(e, "get_user", user_id)

    async def update_user(self, user_id: str, request: UpdateUserRequest) -> UserResponse:
        """Update an existing user.
        
        Args:
            user_id: ID of user to update
            request: Update request data
            
        Returns:
            Updated user response
            
        Raises:
            NotFoundError: If user not found
            ValidationError: If update data is invalid
            ConflictError: If email or username conflicts
        """
        try:
            self._log_operation("update_user", user_id)
            
            # Get existing user
            existing_user = await self.user_repository.get(user_id)
            if not existing_user:
                raise NotFoundError(f"User not found: {user_id}")
            
            # Validate update request
            await self._validate_update_user_request(request, existing_user)
            
            # Apply updates to user entity
            updated_user = self._apply_user_updates(existing_user, request)
            
            # Update in repository
            result = await self.user_repository.update(user_id, updated_user)
            if not result:
                raise NotFoundError(f"User not found: {user_id}")
            
            self._log_operation("update_user_success", user_id)
            return UserResponse.from_entity(result)
            
        except Exception as e:
            self._handle_service_error(e, "update_user", user_id)

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user account.
        
        Args:
            user_id: ID of user to delete
            
        Returns:
            True if user was deleted, False if not found
        """
        try:
            self._log_operation("delete_user", user_id)
            
            # Check if user exists before deletion
            user = await self.user_repository.get(user_id)
            if not user:
                return False
            
            # Perform soft delete by deactivating instead of hard delete
            deactivated_user = await self.user_repository.deactivate_user(user_id)
            
            if deactivated_user and self.notification_service:
                await self._send_account_deactivated_notification(deactivated_user)
            
            self._log_operation("delete_user_success", user_id)
            return deactivated_user is not None
            
        except Exception as e:
            self._handle_service_error(e, "delete_user", user_id)

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        active_only: bool = True
    ) -> UserListResponse:
        """List users with pagination.
        
        Args:
            page: Page number (1-based)
            page_size: Number of users per page
            active_only: Whether to return only active users
            
        Returns:
            Paginated list of users
        """
        try:
            self._log_operation("list_users", context={
                "page": page, "page_size": page_size, "active_only": active_only
            })
            
            if active_only:
                users = await self.user_repository.get_active_users(
                    limit=page_size * 10  # Get more to enable pagination
                )
            else:
                from repository.base import QueryOptions
                options = QueryOptions(
                    limit=page_size * 10,
                    order_by="created_at",
                    order_desc=True
                )
                users = await self.user_repository.list(options)
            
            # Convert to responses
            user_responses = [UserResponse.from_entity(user) for user in users]
            
            # Apply pagination
            paginated = self._paginate_results(user_responses, page, page_size)
            
            return UserListResponse(
                users=paginated["data"],
                pagination=paginated["pagination"]
            )
            
        except Exception as e:
            self._handle_service_error(e, "list_users")

    async def search_users(self, query: str, limit: int = 20) -> List[UserResponse]:
        """Search users by name or email.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            List of matching users
        """
        try:
            self._log_operation("search_users", context={"query": query, "limit": limit})
            
            if not query or len(query.strip()) < 2:
                raise ValidationError("Search query must be at least 2 characters long")
            
            users = await self.user_repository.search_users(query.strip(), limit)
            return [UserResponse.from_entity(user) for user in users]
            
        except Exception as e:
            self._handle_service_error(e, "search_users")

    async def get_user_by_email(self, email: str) -> Optional[UserResponse]:
        """Get user by email address.
        
        Args:
            email: Email address to search for
            
        Returns:
            User response if found, None otherwise
        """
        try:
            self._log_operation("get_user_by_email", context={"email": email})
            
            self._validate_email_format(email)
            
            user = await self.user_repository.get_by_email(email)
            if user:
                return UserResponse.from_entity(user)
            return None
            
        except Exception as e:
            self._handle_service_error(e, "get_user_by_email")

    async def activate_user(self, user_id: str) -> UserResponse:
        """Activate a user account.
        
        Args:
            user_id: ID of user to activate
            
        Returns:
            Updated user response
            
        Raises:
            NotFoundError: If user not found
        """
        try:
            self._log_operation("activate_user", user_id)
            
            activated_user = await self.user_repository.activate_user(user_id)
            if not activated_user:
                raise NotFoundError(f"User not found: {user_id}")
            
            if self.email_service:
                await self._send_account_activated_email(activated_user)
            
            self._log_operation("activate_user_success", user_id)
            return UserResponse.from_entity(activated_user)
            
        except Exception as e:
            self._handle_service_error(e, "activate_user", user_id)

    async def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Change user's password.
        
        Args:
            user_id: ID of user changing password
            old_password: Current password for verification
            new_password: New password to set
            
        Returns:
            True if password changed successfully
            
        Raises:
            NotFoundError: If user not found
            ValidationError: If old password is incorrect or new password is invalid
        """
        try:
            self._log_operation("change_password", user_id)
            
            # Get user
            user = await self.user_repository.get(user_id)
            if not user:
                raise NotFoundError(f"User not found: {user_id}")
            
            # Verify old password
            if not self._verify_password(old_password, user.password_hash):
                raise ValidationError("Current password is incorrect")
            
            # Validate new password
            self._validate_password(new_password)
            
            # Update password
            user.password_hash = self._hash_password(new_password)
            updated_user = await self.user_repository.update(user_id, user)
            
            if updated_user and self.email_service:
                await self._send_password_changed_email(updated_user)
            
            self._log_operation("change_password_success", user_id)
            return updated_user is not None
            
        except Exception as e:
            self._handle_service_error(e, "change_password", user_id)

    # Private helper methods

    async def _validate_create_user_request(self, request: CreateUserRequest) -> None:
        """Validate user creation request."""
        # Basic field validation
        self._validate_required_fields(
            request.__dict__,
            ["username", "email", "password", "full_name"]
        )
        
        # Field length validation
        self._validate_field_length(request.username, "Username", min_length=3, max_length=50)
        self._validate_field_length(request.full_name, "Full name", min_length=2, max_length=100)
        
        # Email format validation
        self._validate_email_format(request.email)
        
        # Password validation
        self._validate_password(request.password)
        
        # Check for uniqueness
        existing_email = await self.user_repository.get_by_email(request.email)
        if existing_email:
            raise ConflictError(f"Email address {request.email} is already registered")
        
        existing_username = await self.user_repository.get_by_username(request.username)
        if existing_username:
            raise ConflictError(f"Username {request.username} is already taken")

    async def _validate_update_user_request(self, request: UpdateUserRequest, existing_user: User) -> None:
        """Validate user update request."""
        if request.email and request.email != existing_user.email:
            self._validate_email_format(request.email)
            existing_email = await self.user_repository.get_by_email(request.email)
            if existing_email and existing_email.id != existing_user.id:
                raise ConflictError(f"Email address {request.email} is already registered")
        
        if request.username and request.username != existing_user.username:
            self._validate_field_length(request.username, "Username", min_length=3, max_length=50)
            existing_username = await self.user_repository.get_by_username(request.username)
            if existing_username and existing_username.id != existing_user.id:
                raise ConflictError(f"Username {request.username} is already taken")
        
        if request.full_name:
            self._validate_field_length(request.full_name, "Full name", min_length=2, max_length=100)

    def _apply_user_updates(self, user: User, request: UpdateUserRequest) -> User:
        """Apply update request to user entity."""
        if request.username:
            user.username = request.username
        if request.email:
            user.email = request.email
        if request.full_name:
            user.full_name = request.full_name
        if request.profile_data is not None:
            user.profile_data = request.profile_data
        return user

    def _validate_password(self, password: str) -> None:
        """Validate password strength."""
        if not password:
            raise ValidationError("Password is required")
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in password):
            raise ValidationError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in password):
            raise ValidationError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in password):
            raise ValidationError("Password must contain at least one digit")

    def _hash_password(self, password: str) -> str:
        """Hash password using secure algorithm."""
        # Use a proper password hashing library like bcrypt or argon2 in production
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}:{password_hash.hex()}"

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify password against stored hash."""
        try:
            salt, hash_value = stored_hash.split(':')
            password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return hash_value == password_hash.hex()
        except ValueError:
            return False

    async def _send_welcome_email(self, user: User) -> None:
        """Send welcome email to new user."""
        if self.email_service:
            try:
                await self.email_service.send_welcome_email(user.email, user.full_name)
                logger.info(f"Welcome email sent to user {user.id}")
            except Exception as e:
                logger.warning(f"Failed to send welcome email to user {user.id}: {e}")

    async def _send_account_activated_email(self, user: User) -> None:
        """Send account activated email."""
        if self.email_service:
            try:
                await self.email_service.send_account_activated_email(user.email, user.full_name)
                logger.info(f"Account activated email sent to user {user.id}")
            except Exception as e:
                logger.warning(f"Failed to send account activated email to user {user.id}: {e}")

    async def _send_password_changed_email(self, user: User) -> None:
        """Send password changed email."""
        if self.email_service:
            try:
                await self.email_service.send_password_changed_email(user.email, user.full_name)
                logger.info(f"Password changed email sent to user {user.id}")
            except Exception as e:
                logger.warning(f"Failed to send password changed email to user {user.id}: {e}")

    async def _send_account_deactivated_notification(self, user: User) -> None:
        """Send account deactivated notification."""
        if self.notification_service:
            try:
                await self.notification_service.send_deactivation_notice(user.id)
                logger.info(f"Deactivation notice sent for user {user.id}")
            except Exception as e:
                logger.warning(f"Failed to send deactivation notice for user {user.id}: {e}")