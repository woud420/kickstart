"""Response Data Transfer Objects.

This module contains DTOs for API responses. These objects serialize
domain entities into appropriate formats for API consumers while
controlling which data is exposed.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

from models.entities.user.user import User
from models.entities.user.profile import UserProfile


@dataclass
class UserResponse:
    """Response DTO for user data.
    
    Provides a safe representation of user data for API responses,
    excluding sensitive information like password hashes.
    """
    id: str
    username: str
    email: str
    full_name: str
    display_name: str
    is_active: bool
    created_at: str
    updated_at: str
    last_login_at: Optional[str]
    profile_data: Dict[str, Any]
    
    # Computed fields
    days_since_creation: int
    has_logged_in: bool

    @classmethod
    def from_entity(cls, user: User) -> 'UserResponse':
        """Create response from User entity.
        
        Args:
            user: User entity to convert
            
        Returns:
            UserResponse instance
        """
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            display_name=user.display_name,
            is_active=user.is_active,
            created_at=user.created_at.isoformat() if user.created_at else "",
            updated_at=user.updated_at.isoformat() if user.updated_at else "",
            last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
            profile_data=user.profile_data.copy(),
            days_since_creation=user.days_since_creation,
            has_logged_in=user.has_logged_in
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'display_name': self.display_name,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'last_login_at': self.last_login_at,
            'profile_data': self.profile_data,
            'days_since_creation': self.days_since_creation,
            'has_logged_in': self.has_logged_in
        }


@dataclass
class PublicUserResponse:
    """Public user response with limited information.
    
    Used when user information is shown to other users,
    containing only publicly visible fields.
    """
    id: str
    username: str
    full_name: str
    display_name: str
    created_at: str

    @classmethod
    def from_entity(cls, user: User) -> 'PublicUserResponse':
        """Create public response from User entity.
        
        Args:
            user: User entity to convert
            
        Returns:
            PublicUserResponse instance
        """
        return cls(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            display_name=user.display_name,
            created_at=user.created_at.isoformat() if user.created_at else ""
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            'id': self.id,
            'username': self.username,
            'full_name': self.full_name,
            'display_name': self.display_name,
            'created_at': self.created_at
        }


@dataclass
class UserProfileResponse:
    """Response DTO for user profile data."""
    user_id: str
    bio: Optional[str]
    avatar_url: Optional[str]
    date_of_birth: Optional[str]
    gender: Optional[str]
    phone: Optional[str]
    timezone: str
    language: str
    visibility: str
    
    # Structured data
    social_links: Dict[str, Optional[str]]
    address: Dict[str, Optional[str]]
    
    # Lists
    interests: List[str]
    skills: List[str]
    
    # Professional info
    occupation: Optional[str]
    company: Optional[str]
    education: Optional[str]
    
    # Timestamps
    created_at: str
    updated_at: str
    
    # Computed fields
    age: Optional[int]
    is_profile_complete: bool
    completion_percentage: int

    @classmethod
    def from_entity(cls, profile: UserProfile) -> 'UserProfileResponse':
        """Create response from UserProfile entity.
        
        Args:
            profile: UserProfile entity to convert
            
        Returns:
            UserProfileResponse instance
        """
        return cls(
            user_id=profile.user_id,
            bio=profile.bio,
            avatar_url=profile.avatar_url,
            date_of_birth=profile.date_of_birth.isoformat() if profile.date_of_birth else None,
            gender=profile.gender.value if profile.gender else None,
            phone=profile.phone,
            timezone=profile.timezone,
            language=profile.language,
            visibility=profile.visibility.value,
            social_links=profile.social_links.to_dict(),
            address=profile.address.to_dict(),
            interests=profile.interests.copy(),
            skills=profile.skills.copy(),
            occupation=profile.occupation,
            company=profile.company,
            education=profile.education,
            created_at=profile.created_at.isoformat() if profile.created_at else "",
            updated_at=profile.updated_at.isoformat() if profile.updated_at else "",
            age=profile.age,
            is_profile_complete=profile.is_profile_complete,
            completion_percentage=profile.completion_percentage
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            'user_id': self.user_id,
            'bio': self.bio,
            'avatar_url': self.avatar_url,
            'date_of_birth': self.date_of_birth,
            'gender': self.gender,
            'phone': self.phone,
            'timezone': self.timezone,
            'language': self.language,
            'visibility': self.visibility,
            'social_links': self.social_links,
            'address': self.address,
            'interests': self.interests,
            'skills': self.skills,
            'occupation': self.occupation,
            'company': self.company,
            'education': self.education,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'age': self.age,
            'is_profile_complete': self.is_profile_complete,
            'completion_percentage': self.completion_percentage
        }


@dataclass
class PaginationMeta:
    """Pagination metadata for list responses."""
    page: int
    page_size: int
    total_count: int
    total_pages: int
    has_next: bool
    has_prev: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            'page': self.page,
            'page_size': self.page_size,
            'total_count': self.total_count,
            'total_pages': self.total_pages,
            'has_next': self.has_next,
            'has_prev': self.has_prev
        }


@dataclass
class UserListResponse:
    """Response DTO for paginated user lists."""
    users: List[UserResponse]
    pagination: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            'users': [user.to_dict() for user in self.users],
            'pagination': self.pagination
        }


@dataclass
class ApiResponse:
    """Generic API response wrapper.
    
    Provides consistent structure for all API responses with
    success/error indication and optional metadata.
    """
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[List[str]] = None
    meta: Optional[Dict[str, Any]] = None

    @classmethod
    def success_response(
        cls, 
        data: Any = None, 
        message: str = "Success",
        meta: Optional[Dict[str, Any]] = None
    ) -> 'ApiResponse':
        """Create a success response.
        
        Args:
            data: Response data
            message: Success message
            meta: Additional metadata
            
        Returns:
            Success ApiResponse instance
        """
        return cls(
            success=True,
            message=message,
            data=data,
            meta=meta
        )

    @classmethod
    def error_response(
        cls,
        message: str,
        errors: Optional[List[str]] = None,
        meta: Optional[Dict[str, Any]] = None
    ) -> 'ApiResponse':
        """Create an error response.
        
        Args:
            message: Error message
            errors: List of specific error messages
            meta: Additional metadata
            
        Returns:
            Error ApiResponse instance
        """
        return cls(
            success=False,
            message=message,
            errors=errors,
            meta=meta
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        response_dict = {
            'success': self.success,
            'message': self.message
        }
        
        if self.data is not None:
            # Convert data to dict if it has to_dict method
            if hasattr(self.data, 'to_dict'):
                response_dict['data'] = self.data.to_dict()
            else:
                response_dict['data'] = self.data
        
        if self.errors:
            response_dict['errors'] = self.errors
        
        if self.meta:
            response_dict['meta'] = self.meta
            
        return response_dict


@dataclass
class CreatedResponse:
    """Response for successful resource creation."""
    id: str
    message: str = "Resource created successfully"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            'id': self.id,
            'message': self.message,
            'success': True
        }


@dataclass
class DeletedResponse:
    """Response for successful resource deletion."""
    message: str = "Resource deleted successfully"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            'message': self.message,
            'success': True
        }


@dataclass
class HealthCheckResponse:
    """Health check response."""
    status: str
    timestamp: str
    version: str
    uptime_seconds: int
    
    @classmethod
    def healthy(cls, version: str, uptime_seconds: int) -> 'HealthCheckResponse':
        """Create healthy response.
        
        Args:
            version: Application version
            uptime_seconds: Application uptime in seconds
            
        Returns:
            Healthy HealthCheckResponse instance
        """
        return cls(
            status="healthy",
            timestamp=datetime.utcnow().isoformat(),
            version=version,
            uptime_seconds=uptime_seconds
        )

    @classmethod
    def unhealthy(cls, version: str) -> 'HealthCheckResponse':
        """Create unhealthy response.
        
        Args:
            version: Application version
            
        Returns:
            Unhealthy HealthCheckResponse instance
        """
        return cls(
            status="unhealthy",
            timestamp=datetime.utcnow().isoformat(),
            version=version,
            uptime_seconds=0
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            'status': self.status,
            'timestamp': self.timestamp,
            'version': self.version,
            'uptime_seconds': self.uptime_seconds
        }