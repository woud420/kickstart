"""Request Data Transfer Objects.

This module contains DTOs (Data Transfer Objects) for handling incoming
requests from API clients. These objects validate and serialize request
data before it's processed by services.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import date

from models.entities.user.user import User
from models.entities.user.profile import Gender, ProfileVisibility


def _require_string(data: Dict[str, object], field_name: str) -> str:
    """Get a required string field from request data."""
    value = data.get(field_name)
    if isinstance(value, str):
        return value
    raise ValueError(f"'{field_name}' must be a string")


def _optional_string(data: Dict[str, object], field_name: str) -> Optional[str]:
    """Get an optional string field from request data."""
    value = data.get(field_name)
    if value is None:
        return None
    if isinstance(value, str):
        return value
    raise ValueError(f"'{field_name}' must be a string when provided")


def _optional_object_dict(data: Dict[str, object], field_name: str) -> Optional[Dict[str, object]]:
    """Get an optional dictionary with string keys from request data."""
    value = data.get(field_name)
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError(f"'{field_name}' must be a dictionary when provided")

    normalized: Dict[str, object] = {}
    for item_key, item_value in value.items():
        if not isinstance(item_key, str):
            raise ValueError(f"'{field_name}' keys must be strings")
        normalized[item_key] = item_value
    return normalized


def _optional_date(data: Dict[str, object], field_name: str) -> Optional[date]:
    """Get an optional ISO date field from request data."""
    value = data.get(field_name)
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value)
    raise ValueError(f"'{field_name}' must be an ISO date string or date")


def _optional_string_list(data: Dict[str, object], field_name: str) -> Optional[List[str]]:
    """Get an optional list of strings from request data."""
    value = data.get(field_name)
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError(f"'{field_name}' must be a list when provided")

    normalized: List[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"'{field_name}' items must be strings")
        normalized.append(item)
    return normalized


def _int_with_default(data: Dict[str, object], field_name: str, default: int) -> int:
    """Get an integer value from request data, using a default when absent."""
    value = data.get(field_name, default)
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value)
    raise ValueError(f"'{field_name}' must be an integer")


@dataclass
class CreateUserRequest:
    """Request DTO for creating a new user.
    
    Contains all required and optional fields for user creation,
    with validation and conversion methods.
    """
    username: str
    email: str
    full_name: str
    password: str
    profile_data: Optional[Dict[str, Any]] = None

    def to_entity(self) -> User:
        """Convert request DTO to User entity.
        
        Returns:
            User entity ready for creation
        """
        return User(
            username=self.username.strip(),
            email=self.email.strip().lower(),
            full_name=self.full_name.strip(),
            password_hash="",  # Will be set by service
            profile_data=self.profile_data or {}
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CreateUserRequest':
        """Create request from dictionary.
        
        Args:
            data: Request data dictionary
            
        Returns:
            CreateUserRequest instance
        """
        return cls(
            username=_require_string(data, 'username'),
            email=_require_string(data, 'email'),
            full_name=_require_string(data, 'full_name'),
            password=_require_string(data, 'password'),
            profile_data=_optional_object_dict(data, 'profile_data')
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excluding password).
        
        Returns:
            Dictionary representation without sensitive data
        """
        return {
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'profile_data': self.profile_data
        }


@dataclass
class UpdateUserRequest:
    """Request DTO for updating an existing user.
    
    All fields are optional to support partial updates.
    """
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    profile_data: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UpdateUserRequest':
        """Create request from dictionary.
        
        Args:
            data: Request data dictionary
            
        Returns:
            UpdateUserRequest instance
        """
        return cls(
            username=_optional_string(data, 'username'),
            email=_optional_string(data, 'email'),
            full_name=_optional_string(data, 'full_name'),
            profile_data=_optional_object_dict(data, 'profile_data')
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'profile_data': self.profile_data
        }

    def has_updates(self) -> bool:
        """Check if request contains any update data.
        
        Returns:
            True if there are fields to update
        """
        return any([
            self.username,
            self.email,
            self.full_name,
            self.profile_data is not None
        ])


@dataclass
class ChangePasswordRequest:
    """Request DTO for changing user password."""
    current_password: str
    new_password: str
    confirm_password: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChangePasswordRequest':
        """Create request from dictionary.
        
        Args:
            data: Request data dictionary
            
        Returns:
            ChangePasswordRequest instance
        """
        return cls(
            current_password=_require_string(data, 'current_password'),
            new_password=_require_string(data, 'new_password'),
            confirm_password=_require_string(data, 'confirm_password')
        )

    def validate_passwords_match(self) -> bool:
        """Validate that new password and confirmation match.
        
        Returns:
            True if passwords match
        """
        return self.new_password == self.confirm_password


@dataclass
class CreateUserProfileRequest:
    """Request DTO for creating or updating user profile."""
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None  # Will be converted to Gender enum
    phone: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    visibility: Optional[str] = None  # Will be converted to ProfileVisibility enum
    
    # Social links
    twitter: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    website: Optional[str] = None
    instagram: Optional[str] = None
    facebook: Optional[str] = None
    
    # Address information
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    
    # Lists
    interests: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    
    # Professional info
    occupation: Optional[str] = None
    company: Optional[str] = None
    education: Optional[str] = None

    @property
    def parsed_gender(self) -> Optional[Gender]:
        """Get Gender enum from string value.
        
        Returns:
            Gender enum value or None
        """
        if self.gender:
            try:
                return Gender(self.gender.lower())
            except ValueError:
                return None
        return None

    @property
    def parsed_visibility(self) -> ProfileVisibility:
        """Get ProfileVisibility enum from string value.
        
        Returns:
            ProfileVisibility enum value, defaults to PUBLIC
        """
        if self.visibility:
            try:
                return ProfileVisibility(self.visibility.lower())
            except ValueError:
                return ProfileVisibility.PUBLIC
        return ProfileVisibility.PUBLIC

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CreateUserProfileRequest':
        """Create request from dictionary.
        
        Args:
            data: Request data dictionary
            
        Returns:
            CreateUserProfileRequest instance
        """
        date_of_birth = _optional_date(data, 'date_of_birth')

        return cls(
            bio=_optional_string(data, 'bio'),
            avatar_url=_optional_string(data, 'avatar_url'),
            date_of_birth=date_of_birth,
            gender=_optional_string(data, 'gender'),
            phone=_optional_string(data, 'phone'),
            timezone=_optional_string(data, 'timezone'),
            language=_optional_string(data, 'language'),
            visibility=_optional_string(data, 'visibility'),
            twitter=_optional_string(data, 'twitter'),
            linkedin=_optional_string(data, 'linkedin'),
            github=_optional_string(data, 'github'),
            website=_optional_string(data, 'website'),
            instagram=_optional_string(data, 'instagram'),
            facebook=_optional_string(data, 'facebook'),
            street=_optional_string(data, 'street'),
            city=_optional_string(data, 'city'),
            state=_optional_string(data, 'state'),
            country=_optional_string(data, 'country'),
            postal_code=_optional_string(data, 'postal_code'),
            interests=_optional_string_list(data, 'interests'),
            skills=_optional_string_list(data, 'skills'),
            occupation=_optional_string(data, 'occupation'),
            company=_optional_string(data, 'company'),
            education=_optional_string(data, 'education')
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            'bio': self.bio,
            'avatar_url': self.avatar_url,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'gender': self.gender,
            'phone': self.phone,
            'timezone': self.timezone,
            'language': self.language,
            'visibility': self.visibility,
            'social_links': {
                'twitter': self.twitter,
                'linkedin': self.linkedin,
                'github': self.github,
                'website': self.website,
                'instagram': self.instagram,
                'facebook': self.facebook
            },
            'address': {
                'street': self.street,
                'city': self.city,
                'state': self.state,
                'country': self.country,
                'postal_code': self.postal_code
            },
            'interests': self.interests,
            'skills': self.skills,
            'occupation': self.occupation,
            'company': self.company,
            'education': self.education
        }


@dataclass
class ListUsersRequest:
    """Request DTO for listing users with filtering and pagination."""
    page: int = 1
    page_size: int = 20
    active_only: bool = True
    search_query: Optional[str] = None
    order_by: Optional[str] = None
    order_desc: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ListUsersRequest':
        """Create request from dictionary.
        
        Args:
            data: Request data dictionary
            
        Returns:
            ListUsersRequest instance
        """
        return cls(
            page=max(1, _int_with_default(data, 'page', 1)),
            page_size=min(100, max(1, _int_with_default(data, 'page_size', 20))),
            active_only=bool(data.get('active_only', True)),
            search_query=_optional_string(data, 'search_query'),
            order_by=_optional_string(data, 'order_by'),
            order_desc=bool(data.get('order_desc', False))
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            'page': self.page,
            'page_size': self.page_size,
            'active_only': self.active_only,
            'search_query': self.search_query,
            'order_by': self.order_by,
            'order_desc': self.order_desc
        }


@dataclass
class SearchUsersRequest:
    """Request DTO for searching users."""
    query: str
    limit: int = 20

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchUsersRequest':
        """Create request from dictionary.
        
        Args:
            data: Request data dictionary
            
        Returns:
            SearchUsersRequest instance
        """
        return cls(
            query=_require_string(data, 'query').strip(),
            limit=min(100, max(1, _int_with_default(data, 'limit', 20)))
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            'query': self.query,
            'limit': self.limit
        }
