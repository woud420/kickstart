"""Model layer for data structures and entities.

This module contains all data-related structures including:
- Domain entities (business objects)
- Data Transfer Objects (DTOs) for API communication
- Pydantic schemas for validation and serialization

The models are organized to separate concerns:
- entities/: Core domain models with business logic
- dto/: Request/response objects for API layers
- schemas.py: Pydantic models for validation
"""

from .entities import *
from .dto import *

__all__ = [
    # Domain entities
    "User",
    "UserProfile",
    "ProfileVisibility",
    "Gender",
    "SocialLinks",
    "Address",
    
    # Request DTOs
    "CreateUserRequest",
    "UpdateUserRequest",
    "ChangePasswordRequest", 
    "CreateUserProfileRequest",
    "ListUsersRequest",
    "SearchUsersRequest",
    
    # Response DTOs
    "UserResponse",
    "PublicUserResponse",
    "UserProfileResponse",
    "UserListResponse",
    "PaginationMeta",
    "ApiResponse",
    "CreatedResponse",
    "DeletedResponse",
    "HealthCheckResponse",
]