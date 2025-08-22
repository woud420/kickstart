"""Pydantic schemas for data validation and serialization.

This module contains Pydantic models that provide runtime validation,
serialization, and documentation for API data structures. These schemas
are used primarily with FastAPI for automatic request/response validation.
"""

from pydantic import BaseModel, Field, EmailStr, validator, root_validator
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from enum import Enum


class GenderSchema(str, Enum):
    """Gender options schema."""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class ProfileVisibilitySchema(str, Enum):
    """Profile visibility options schema."""
    PUBLIC = "public"
    FRIENDS = "friends"
    PRIVATE = "private"


class CreateUserSchema(BaseModel):
    """Schema for user creation requests."""
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="User's email address")
    full_name: str = Field(..., min_length=2, max_length=100, description="User's full name")
    password: str = Field(..., min_length=8, max_length=128, description="User password")
    profile_data: Optional[Dict[str, Any]] = Field(default=None, description="Additional profile data")

    @validator('username')
    def validate_username(cls, v):
        """Validate username format."""
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and dashes')
        
        # Reserved usernames
        reserved = {'admin', 'administrator', 'root', 'system', 'api', 'www'}
        if v.lower() in reserved:
            raise ValueError('This username is reserved')
        return v

    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError('Password must contain at least one special character')
        return v

    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "password": "SecurePass123!",
                "profile_data": {
                    "bio": "Software developer"
                }
            }
        }


class UpdateUserSchema(BaseModel):
    """Schema for user update requests."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    profile_data: Optional[Dict[str, Any]] = None

    @validator('username')
    def validate_username(cls, v):
        """Validate username format."""
        if v is None:
            return v
        
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and dashes')
        
        reserved = {'admin', 'administrator', 'root', 'system', 'api', 'www'}
        if v.lower() in reserved:
            raise ValueError('This username is reserved')
        return v

    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "full_name": "John Smith",
                "profile_data": {
                    "bio": "Senior software developer"
                }
            }
        }


class ChangePasswordSchema(BaseModel):
    """Schema for password change requests."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    confirm_password: str = Field(..., description="Confirm new password")

    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError('Password must contain at least one special character')
        return v

    @root_validator
    def validate_passwords_match(cls, values):
        """Validate that passwords match."""
        new_password = values.get('new_password')
        confirm_password = values.get('confirm_password')
        
        if new_password and confirm_password and new_password != confirm_password:
            raise ValueError('New password and confirmation do not match')
        return values

    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "current_password": "OldPass123!",
                "new_password": "NewSecurePass123!",
                "confirm_password": "NewSecurePass123!"
            }
        }


class SocialLinksSchema(BaseModel):
    """Schema for social media links."""
    twitter: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    website: Optional[str] = None
    instagram: Optional[str] = None
    facebook: Optional[str] = None

    @validator('twitter', 'linkedin', 'github', 'website', 'instagram', 'facebook')
    def validate_url(cls, v):
        """Validate URL format."""
        if v is None:
            return v
        
        import re
        url_pattern = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(v):
            raise ValueError('Must be a valid URL')
        return v


class AddressSchema(BaseModel):
    """Schema for address information."""
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None


class UserProfileSchema(BaseModel):
    """Schema for user profile requests."""
    bio: Optional[str] = Field(None, max_length=500, description="User biography")
    avatar_url: Optional[str] = Field(None, description="URL to profile picture")
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    gender: Optional[GenderSchema] = None
    phone: Optional[str] = Field(None, description="Phone number")
    timezone: Optional[str] = Field(default="UTC", description="User timezone")
    language: Optional[str] = Field(default="en", description="Preferred language")
    visibility: Optional[ProfileVisibilitySchema] = Field(default=ProfileVisibilitySchema.PUBLIC)
    
    social_links: Optional[SocialLinksSchema] = None
    address: Optional[AddressSchema] = None
    
    interests: Optional[List[str]] = Field(default=[], description="User interests")
    skills: Optional[List[str]] = Field(default=[], description="User skills")
    
    occupation: Optional[str] = Field(None, max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    education: Optional[str] = Field(None, max_length=200)

    @validator('date_of_birth')
    def validate_date_of_birth(cls, v):
        """Validate date of birth."""
        if v is None:
            return v
        
        from datetime import date
        today = date.today()
        
        if v > today:
            raise ValueError('Date of birth cannot be in the future')
        
        age_years = (today - v).days / 365.25
        if age_years > 150:
            raise ValueError('Date of birth is too far in the past')
        if age_years < 13:
            raise ValueError('Users must be at least 13 years old')
        
        return v

    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number."""
        if v is None:
            return v
        
        import re
        # Remove common separators
        clean_phone = re.sub(r'[\s\-\(\)\.]+', '', v)
        
        # Simple international format validation
        if not re.match(r'^\+?[1-9]\d{1,14}$', clean_phone):
            raise ValueError('Phone number must be in international format')
        
        return v

    @validator('interests', 'skills')
    def validate_lists(cls, v):
        """Validate interest and skill lists."""
        if v is None:
            return []
        
        # Remove empty strings and duplicates
        cleaned = list(dict.fromkeys([item.strip() for item in v if item and item.strip()]))
        
        # Limit number of items
        if len(cleaned) > 20:
            raise ValueError('Maximum 20 items allowed')
        
        return cleaned

    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "bio": "Software developer passionate about clean code",
                "avatar_url": "https://example.com/avatar.jpg",
                "date_of_birth": "1990-01-01",
                "gender": "male",
                "phone": "+1234567890",
                "timezone": "America/New_York",
                "language": "en",
                "visibility": "public",
                "social_links": {
                    "github": "https://github.com/johndoe",
                    "linkedin": "https://linkedin.com/in/johndoe"
                },
                "address": {
                    "city": "New York",
                    "country": "USA"
                },
                "interests": ["programming", "music", "travel"],
                "skills": ["python", "javascript", "docker"],
                "occupation": "Software Engineer",
                "company": "Tech Corp"
            }
        }


class ListUsersSchema(BaseModel):
    """Schema for listing users with pagination."""
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    active_only: bool = Field(default=True, description="Show only active users")
    search_query: Optional[str] = Field(None, min_length=2, description="Search query")
    order_by: Optional[str] = Field(None, description="Field to order by")
    order_desc: bool = Field(default=False, description="Order descending")

    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "page": 1,
                "page_size": 20,
                "active_only": True,
                "search_query": "john",
                "order_by": "created_at",
                "order_desc": True
            }
        }


class SearchUsersSchema(BaseModel):
    """Schema for searching users."""
    query: str = Field(..., min_length=2, max_length=100, description="Search query")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum results")

    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "query": "john doe",
                "limit": 10
            }
        }


class UserResponseSchema(BaseModel):
    """Schema for user response data."""
    id: str
    username: str
    email: str
    full_name: str
    display_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime]
    profile_data: Dict[str, Any]
    days_since_creation: int
    has_logged_in: bool

    class Config:
        """Pydantic config."""
        orm_mode = True


class PublicUserResponseSchema(BaseModel):
    """Schema for public user response data."""
    id: str
    username: str
    full_name: str
    display_name: str
    created_at: datetime

    class Config:
        """Pydantic config."""
        orm_mode = True


class PaginationMetaSchema(BaseModel):
    """Schema for pagination metadata."""
    page: int
    page_size: int
    total_count: int
    total_pages: int
    has_next: bool
    has_prev: bool


class UserListResponseSchema(BaseModel):
    """Schema for paginated user list response."""
    users: List[UserResponseSchema]
    pagination: PaginationMetaSchema


class ApiResponseSchema(BaseModel):
    """Schema for generic API response."""
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[List[str]] = None
    meta: Optional[Dict[str, Any]] = None


class ErrorResponseSchema(BaseModel):
    """Schema for error responses."""
    success: bool = False
    message: str
    errors: Optional[List[str]] = None
    error_code: Optional[str] = None

    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "success": False,
                "message": "Validation failed",
                "errors": [
                    "Username is required",
                    "Email format is invalid"
                ],
                "error_code": "VALIDATION_ERROR"
            }
        }


class HealthCheckResponseSchema(BaseModel):
    """Schema for health check response."""
    status: str
    timestamp: datetime
    version: str
    uptime_seconds: int

    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2023-01-01T12:00:00Z",
                "version": "1.0.0",
                "uptime_seconds": 3600
            }
        }