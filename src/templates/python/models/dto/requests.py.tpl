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
            username=data['username'],
            email=data['email'],
            full_name=data['full_name'],
            password=data['password'],
            profile_data=data.get('profile_data')
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
            username=data.get('username'),
            email=data.get('email'),
            full_name=data.get('full_name'),
            profile_data=data.get('profile_data')
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
            current_password=data['current_password'],
            new_password=data['new_password'],
            confirm_password=data['confirm_password']
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
        # Parse date of birth if provided
        date_of_birth = None
        if data.get('date_of_birth'):
            if isinstance(data['date_of_birth'], str):
                date_of_birth = date.fromisoformat(data['date_of_birth'])
            else:
                date_of_birth = data['date_of_birth']

        return cls(
            bio=data.get('bio'),
            avatar_url=data.get('avatar_url'),
            date_of_birth=date_of_birth,
            gender=data.get('gender'),
            phone=data.get('phone'),
            timezone=data.get('timezone'),
            language=data.get('language'),
            visibility=data.get('visibility'),
            twitter=data.get('twitter'),
            linkedin=data.get('linkedin'),
            github=data.get('github'),
            website=data.get('website'),
            instagram=data.get('instagram'),
            facebook=data.get('facebook'),
            street=data.get('street'),
            city=data.get('city'),
            state=data.get('state'),
            country=data.get('country'),
            postal_code=data.get('postal_code'),
            interests=data.get('interests'),
            skills=data.get('skills'),
            occupation=data.get('occupation'),
            company=data.get('company'),
            education=data.get('education')
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
            page=max(1, int(data.get('page', 1))),
            page_size=min(100, max(1, int(data.get('page_size', 20)))),
            active_only=bool(data.get('active_only', True)),
            search_query=data.get('search_query'),
            order_by=data.get('order_by'),
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
            query=data['query'].strip(),
            limit=min(100, max(1, int(data.get('limit', 20))))
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