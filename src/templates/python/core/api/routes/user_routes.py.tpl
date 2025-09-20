"""User API routes using FastAPI.

This module defines the REST API endpoints for user operations.
It uses dependency injection to receive services and handles
request/response transformation via DTOs.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from typing import List, Optional
import logging

from core.services.user_service import UserService
from core.services.exceptions import (
    ValidationError,
    NotFoundError,
    ConflictError,
    ServiceError
)
from models.dto.requests import (
    CreateUserRequest,
    UpdateUserRequest,
    ChangePasswordRequest,
    ListUsersRequest,
    SearchUsersRequest
)
from models.dto.responses import (
    UserResponse,
    PublicUserResponse,
    UserListResponse,
    ApiResponse,
    CreatedResponse
)
from models.schemas import (
    CreateUserSchema,
    UpdateUserSchema,
    ChangePasswordSchema,
    ListUsersSchema,
    SearchUsersSchema,
    UserResponseSchema,
    PublicUserResponseSchema,
    UserListResponseSchema,
    ApiResponseSchema,
    ErrorResponseSchema
)
from api.dependencies import get_user_service, get_current_user

logger = logging.getLogger(__name__)

# Create router with prefix and tags
router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={
        404: {"model": ErrorResponseSchema, "description": "Not found"},
        422: {"model": ErrorResponseSchema, "description": "Validation error"},
        500: {"model": ErrorResponseSchema, "description": "Internal server error"}
    }
)


@router.post(
    "/",
    response_model=ApiResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Create a new user account with the provided information"
)
async def create_user(
    user_data: CreateUserSchema,
    user_service: UserService = Depends(get_user_service)
) -> ApiResponseSchema:
    """Create a new user account.
    
    Args:
        user_data: User creation data
        user_service: Injected user service
        
    Returns:
        API response with created user information
        
    Raises:
        HTTPException: If creation fails due to validation or conflicts
    """
    try:
        logger.info(f"Creating user with username: {user_data.username}")
        
        # Convert Pydantic model to DTO
        request = CreateUserRequest(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            password=user_data.password,
            profile_data=user_data.profile_data
        )
        
        # Create user via service
        user_response = await user_service.create_user(request)
        
        return ApiResponse.success_response(
            data=user_response.to_dict(),
            message="User created successfully"
        )
        
    except ValidationError as e:
        logger.warning(f"User creation validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except ConflictError as e:
        logger.warning(f"User creation conflict: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ServiceError as e:
        logger.error(f"User creation service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.get(
    "/{user_id}",
    response_model=UserResponseSchema,
    summary="Get user by ID",
    description="Retrieve a specific user by their unique identifier"
)
async def get_user(
    user_id: str = Path(..., description="User ID"),
    user_service: UserService = Depends(get_user_service)
) -> UserResponseSchema:
    """Get a user by ID.
    
    Args:
        user_id: User ID to retrieve
        user_service: Injected user service
        
    Returns:
        User response data
        
    Raises:
        HTTPException: If user not found or service error
    """
    try:
        logger.info(f"Getting user: {user_id}")
        
        user_response = await user_service.get_user(user_id)
        
        # Convert to Pydantic model for response validation
        return UserResponseSchema(**user_response.to_dict())
        
    except NotFoundError as e:
        logger.warning(f"User not found: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ServiceError as e:
        logger.error(f"Get user service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )


@router.put(
    "/{user_id}",
    response_model=UserResponseSchema,
    summary="Update user",
    description="Update an existing user's information"
)
async def update_user(
    user_id: str = Path(..., description="User ID"),
    user_data: UpdateUserSchema = None,
    user_service: UserService = Depends(get_user_service),
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponseSchema:
    """Update a user.
    
    Args:
        user_id: User ID to update
        user_data: Updated user data
        user_service: Injected user service
        current_user: Current authenticated user
        
    Returns:
        Updated user response data
        
    Raises:
        HTTPException: If user not found, unauthorized, or validation error
    """
    try:
        # Authorization check - users can only update themselves
        if current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own profile"
            )
        
        logger.info(f"Updating user: {user_id}")
        
        # Convert Pydantic model to DTO
        request = UpdateUserRequest(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            profile_data=user_data.profile_data
        )
        
        user_response = await user_service.update_user(user_id, request)
        
        return UserResponseSchema(**user_response.to_dict())
        
    except NotFoundError as e:
        logger.warning(f"User not found for update: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        logger.warning(f"User update validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except ConflictError as e:
        logger.warning(f"User update conflict: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ServiceError as e:
        logger.error(f"Update user service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.delete(
    "/{user_id}",
    response_model=ApiResponseSchema,
    summary="Delete user",
    description="Delete (deactivate) a user account"
)
async def delete_user(
    user_id: str = Path(..., description="User ID"),
    user_service: UserService = Depends(get_user_service),
    current_user: UserResponse = Depends(get_current_user)
) -> ApiResponseSchema:
    """Delete (deactivate) a user account.
    
    Args:
        user_id: User ID to delete
        user_service: Injected user service
        current_user: Current authenticated user
        
    Returns:
        Deletion confirmation response
        
    Raises:
        HTTPException: If unauthorized or service error
    """
    try:
        # Authorization check - users can only delete themselves
        if current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own account"
            )
        
        logger.info(f"Deleting user: {user_id}")
        
        deleted = await user_service.delete_user(user_id)
        
        if deleted:
            return ApiResponse.success_response(
                message="User account deactivated successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
    except ServiceError as e:
        logger.error(f"Delete user service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )


@router.get(
    "/",
    response_model=UserListResponseSchema,
    summary="List users",
    description="Get a paginated list of users"
)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    active_only: bool = Query(True, description="Show only active users"),
    search_query: Optional[str] = Query(None, min_length=2, description="Search query"),
    user_service: UserService = Depends(get_user_service)
) -> UserListResponseSchema:
    """List users with pagination and filtering.
    
    Args:
        page: Page number (1-based)
        page_size: Number of items per page
        active_only: Whether to show only active users
        search_query: Optional search query
        user_service: Injected user service
        
    Returns:
        Paginated list of users
        
    Raises:
        HTTPException: If service error occurs
    """
    try:
        logger.info(f"Listing users: page={page}, page_size={page_size}, active_only={active_only}")
        
        user_list_response = await user_service.list_users(
            page=page,
            page_size=page_size,
            active_only=active_only
        )
        
        return UserListResponseSchema(**user_list_response.to_dict())
        
    except ServiceError as e:
        logger.error(f"List users service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.get(
    "/search",
    response_model=List[PublicUserResponseSchema],
    summary="Search users",
    description="Search users by name, username, or email"
)
async def search_users(
    query: str = Query(..., min_length=2, max_length=100, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    user_service: UserService = Depends(get_user_service)
) -> List[PublicUserResponseSchema]:
    """Search users by query string.
    
    Args:
        query: Search query
        limit: Maximum number of results
        user_service: Injected user service
        
    Returns:
        List of matching users (public info only)
        
    Raises:
        HTTPException: If validation or service error occurs
    """
    try:
        logger.info(f"Searching users with query: {query}")
        
        request = SearchUsersRequest(query=query, limit=limit)
        user_responses = await user_service.search_users(query, limit)
        
        # Convert to public responses for privacy
        public_responses = []
        for user_response in user_responses:
            public_response = PublicUserResponse(
                id=user_response.id,
                username=user_response.username,
                full_name=user_response.full_name,
                display_name=user_response.display_name,
                created_at=user_response.created_at
            )
            public_responses.append(PublicUserResponseSchema(**public_response.to_dict()))
        
        return public_responses
        
    except ValidationError as e:
        logger.warning(f"User search validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except ServiceError as e:
        logger.error(f"Search users service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search users"
        )


@router.post(
    "/{user_id}/change-password",
    response_model=ApiResponseSchema,
    summary="Change user password",
    description="Change the password for a user account"
)
async def change_password(
    user_id: str = Path(..., description="User ID"),
    password_data: ChangePasswordSchema = None,
    user_service: UserService = Depends(get_user_service),
    current_user: UserResponse = Depends(get_current_user)
) -> ApiResponseSchema:
    """Change user password.
    
    Args:
        user_id: User ID
        password_data: Password change data
        user_service: Injected user service
        current_user: Current authenticated user
        
    Returns:
        Password change confirmation
        
    Raises:
        HTTPException: If unauthorized, validation error, or service error
    """
    try:
        # Authorization check - users can only change their own password
        if current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only change your own password"
            )
        
        logger.info(f"Changing password for user: {user_id}")
        
        success = await user_service.change_password(
            user_id,
            password_data.current_password,
            password_data.new_password
        )
        
        if success:
            return ApiResponse.success_response(
                message="Password changed successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
    except ValidationError as e:
        logger.warning(f"Password change validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except ServiceError as e:
        logger.error(f"Change password service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.post(
    "/{user_id}/activate",
    response_model=UserResponseSchema,
    summary="Activate user",
    description="Activate a deactivated user account"
)
async def activate_user(
    user_id: str = Path(..., description="User ID"),
    user_service: UserService = Depends(get_user_service),
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponseSchema:
    """Activate a user account.
    
    Args:
        user_id: User ID to activate
        user_service: Injected user service
        current_user: Current authenticated user
        
    Returns:
        Activated user response
        
    Raises:
        HTTPException: If unauthorized, not found, or service error
    """
    try:
        # Authorization check - users can only activate themselves
        # In a real app, this might be restricted to admin users
        if current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only activate your own account"
            )
        
        logger.info(f"Activating user: {user_id}")
        
        user_response = await user_service.activate_user(user_id)
        
        return UserResponseSchema(**user_response.to_dict())
        
    except NotFoundError as e:
        logger.warning(f"User not found for activation: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ServiceError as e:
        logger.error(f"Activate user service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate user"
        )


@router.get(
    "/email/{email}",
    response_model=PublicUserResponseSchema,
    summary="Get user by email",
    description="Find a user by their email address (returns public info only)"
)
async def get_user_by_email(
    email: str = Path(..., description="User email address"),
    user_service: UserService = Depends(get_user_service)
) -> PublicUserResponseSchema:
    """Get user by email address.
    
    Args:
        email: Email address to search for
        user_service: Injected user service
        
    Returns:
        Public user information
        
    Raises:
        HTTPException: If user not found or service error
    """
    try:
        logger.info(f"Getting user by email: {email}")
        
        user_response = await user_service.get_user_by_email(email)
        
        if user_response is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Convert to public response for privacy
        public_response = PublicUserResponse(
            id=user_response.id,
            username=user_response.username,
            full_name=user_response.full_name,
            display_name=user_response.display_name,
            created_at=user_response.created_at
        )
        
        return PublicUserResponseSchema(**public_response.to_dict())
        
    except ValidationError as e:
        logger.warning(f"Email validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except ServiceError as e:
        logger.error(f"Get user by email service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )