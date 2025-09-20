"""Data Transfer Objects for API communication.

This module contains DTOs for handling data exchange between API layers
and services. DTOs provide validation, serialization, and transformation
of data between different application layers.
"""

{% block imports %}
from .requests import (
    CreateUserRequest,
    UpdateUserRequest,
    ChangePasswordRequest,
    CreateUserProfileRequest,
    ListUsersRequest,
    SearchUsersRequest
)
from .responses import (
    UserResponse,
    PublicUserResponse,
    UserProfileResponse,
    UserListResponse,
    PaginationMeta,
    ApiResponse,
    CreatedResponse,
    DeletedResponse,
    HealthCheckResponse
)
{% endblock %}

{% block exports %}
__all__ = [
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
{% endblock %}