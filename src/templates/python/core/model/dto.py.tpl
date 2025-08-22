"""Data Transfer Objects (DTOs) for API requests and responses.

DTOs define the structure of data exchanged between the API and clients.
These are simple dataclasses that handle serialization/deserialization.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime


# Request DTOs
@dataclass
class CreateUserRequest:
    """Request DTO for creating a new user."""
    
    username: str
    email: str
    full_name: str = ""
    profile_data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate request data."""
        if not self.username:
            raise ValueError("Username is required")
        if not self.email:
            raise ValueError("Email is required")
        if "@" not in self.email:
            raise ValueError("Invalid email format")
        if len(self.username) < 3:
            raise ValueError("Username must be at least 3 characters")
        if len(self.username) > 50:
            raise ValueError("Username cannot exceed 50 characters")


@dataclass
class UpdateUserRequest:
    """Request DTO for updating a user."""
    
    full_name: Optional[str] = None
    profile_data: Optional[Dict[str, Any]] = None
    
    def has_updates(self) -> bool:
        """Check if the request contains any updates."""
        return any([
            self.full_name is not None,
            self.profile_data is not None
        ])


@dataclass
class CreateUserProfileRequest:
    """Request DTO for creating a user profile."""
    
    bio: str = ""
    avatar_url: str = ""
    location: str = ""
    website: str = ""
    social_links: Dict[str, str] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UpdateUserProfileRequest:
    """Request DTO for updating a user profile."""
    
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    social_links: Optional[Dict[str, str]] = None
    preferences: Optional[Dict[str, Any]] = None
    
    def has_updates(self) -> bool:
        """Check if the request contains any updates."""
        return any([
            self.bio is not None,
            self.avatar_url is not None,
            self.location is not None,
            self.website is not None,
            self.social_links is not None,
            self.preferences is not None
        ])


# Response DTOs
@dataclass
class UserResponse:
    """Response DTO for user data."""
    
    id: str
    username: str
    email: str
    full_name: str
    is_active: bool
    created_at: str
    updated_at: str
    last_login_at: Optional[str] = None
    profile_data: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_entity(cls, user) -> "UserResponse":
        """Create response from user entity."""
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at.isoformat() if user.created_at else "",
            updated_at=user.updated_at.isoformat() if user.updated_at else "",
            last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
            profile_data=user.profile_data
        )


@dataclass
class UserProfileResponse:
    """Response DTO for user profile data."""
    
    user_id: str
    bio: str
    avatar_url: str
    location: str
    website: str
    social_links: Dict[str, str]
    preferences: Dict[str, Any]
    created_at: str
    updated_at: str
    
    @classmethod
    def from_entity(cls, profile) -> "UserProfileResponse":
        """Create response from user profile entity."""
        return cls(
            user_id=profile.user_id,
            bio=profile.bio,
            avatar_url=profile.avatar_url,
            location=profile.location,
            website=profile.website,
            social_links=profile.social_links,
            preferences=profile.preferences,
            created_at=profile.created_at.isoformat() if profile.created_at else "",
            updated_at=profile.updated_at.isoformat() if profile.updated_at else ""
        )


@dataclass
class UserListResponse:
    """Response DTO for list of users."""
    
    users: List[UserResponse]
    total: int
    page: int = 1
    page_size: int = 10
    has_next: bool = False
    has_previous: bool = False
    
    @classmethod
    def from_entities(cls, users: List, total: int = None, page: int = 1, page_size: int = 10) -> "UserListResponse":
        """Create response from list of user entities."""
        user_responses = [UserResponse.from_entity(user) for user in users]
        total_count = total if total is not None else len(users)
        
        return cls(
            users=user_responses,
            total=total_count,
            page=page,
            page_size=page_size,
            has_next=(page * page_size) < total_count,
            has_previous=page > 1
        )


# Generic Response DTOs
@dataclass
class ApiResponse:
    """Generic API response DTO."""
    
    success: bool
    message: str = ""
    data: Any = None
    error_code: Optional[str] = None
    
    @classmethod
    def success_response(cls, data: Any = None, message: str = "Success") -> "ApiResponse":
        """Create a success response."""
        return cls(success=True, data=data, message=message)
    
    @classmethod
    def error_response(cls, message: str, error_code: str = None) -> "ApiResponse":
        """Create an error response."""
        return cls(success=False, message=message, error_code=error_code)


@dataclass
class ErrorResponse:
    """Error response DTO."""
    
    success: bool = False
    message: str = ""
    error_code: str = ""
    details: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class HealthCheckResponse:
    """Health check response DTO."""
    
    healthy: bool
    service: str
    version: str
    checks: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# Pagination DTOs
@dataclass
class PaginationRequest:
    """Request DTO for pagination parameters."""
    
    page: int = 1
    page_size: int = 10
    sort_by: str = "created_at"
    sort_order: str = "desc"  # "asc" or "desc"
    
    def __post_init__(self):
        """Validate pagination parameters."""
        if self.page < 1:
            self.page = 1
        if self.page_size < 1:
            self.page_size = 10
        if self.page_size > 100:
            self.page_size = 100
        if self.sort_order not in ["asc", "desc"]:
            self.sort_order = "desc"
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.page_size


@dataclass
class PaginationResponse:
    """Response DTO for pagination metadata."""
    
    page: int
    page_size: int
    total: int
    total_pages: int
    has_next: bool
    has_previous: bool
    
    @classmethod
    def from_request(cls, request: PaginationRequest, total: int) -> "PaginationResponse":
        """Create pagination response from request and total count."""
        total_pages = (total + request.page_size - 1) // request.page_size
        
        return cls(
            page=request.page,
            page_size=request.page_size,
            total=total,
            total_pages=total_pages,
            has_next=request.page < total_pages,
            has_previous=request.page > 1
        )