"""User entity model.

This module defines the User entity which represents a user in the domain model.
The entity contains all the business data and behavior related to users,
independent of storage or presentation concerns.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
import uuid


@dataclass
class User:
    """User entity representing a user in the system.
    
    This is the core domain entity for users, containing all user-related
    data and business rules. It's used throughout the application layers
    but is independent of storage or presentation details.
    
    Attributes:
        id: Unique identifier for the user
        username: Unique username for login
        email: Unique email address
        full_name: User's full display name
        password_hash: Hashed password (never store plain text)
        is_active: Whether the user account is active
        created_at: When the user account was created
        updated_at: When the user account was last updated
        last_login_at: When the user last logged in
        deactivated_at: When the user account was deactivated (if applicable)
        profile_data: Additional profile information as JSON
    """
    
    # Core identity fields
    username: str
    email: str
    full_name: str
    password_hash: str
    
    # Status and flags
    is_active: bool = True
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    deactivated_at: Optional[datetime] = None
    
    # Optional fields
    id: Optional[str] = field(default_factory=lambda: str(uuid.uuid4()))
    profile_data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Post-initialization validation and setup."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = self.created_at

    @property
    def display_name(self) -> str:
        """Get the preferred display name for the user.
        
        Returns:
            User's full name or username as fallback
        """
        return self.full_name or self.username

    @property
    def is_deactivated(self) -> bool:
        """Check if the user account is deactivated.
        
        Returns:
            True if user is deactivated, False otherwise
        """
        return self.deactivated_at is not None

    @property
    def days_since_creation(self) -> int:
        """Get number of days since account creation.
        
        Returns:
            Number of days since account was created
        """
        if not self.created_at:
            return 0
        return (datetime.utcnow() - self.created_at).days

    @property
    def has_logged_in(self) -> bool:
        """Check if user has ever logged in.
        
        Returns:
            True if user has logged in at least once
        """
        return self.last_login_at is not None

    def deactivate(self) -> None:
        """Deactivate the user account.
        
        Sets the account to inactive and records the deactivation timestamp.
        This is a soft delete that preserves user data.
        """
        self.is_active = False
        self.deactivated_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """Activate the user account.
        
        Sets the account to active and clears the deactivation timestamp.
        """
        self.is_active = True
        self.deactivated_at = None
        self.updated_at = datetime.utcnow()

    def update_last_login(self) -> None:
        """Update the last login timestamp to current time."""
        self.last_login_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def update_profile(self, profile_data: Dict[str, Any]) -> None:
        """Update user profile data.
        
        Args:
            profile_data: Dictionary of profile fields to update
        """
        if profile_data:
            self.profile_data.update(profile_data)
            self.updated_at = datetime.utcnow()

    def get_profile_field(self, field: str, default: Any = None) -> Any:
        """Get a specific profile field value.
        
        Args:
            field: Profile field name
            default: Default value if field doesn't exist
            
        Returns:
            Profile field value or default
        """
        return self.profile_data.get(field, default)

    def has_profile_field(self, field: str) -> bool:
        """Check if a profile field exists.
        
        Args:
            field: Profile field name
            
        Returns:
            True if field exists in profile data
        """
        return field in self.profile_data

    def remove_profile_field(self, field: str) -> bool:
        """Remove a profile field.
        
        Args:
            field: Profile field name to remove
            
        Returns:
            True if field was removed, False if it didn't exist
        """
        if field in self.profile_data:
            del self.profile_data[field]
            self.updated_at = datetime.utcnow()
            return True
        return False

    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert user entity to dictionary.
        
        Args:
            include_sensitive: Whether to include sensitive fields like password_hash
            
        Returns:
            Dictionary representation of user
        """
        user_dict = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'deactivated_at': self.deactivated_at.isoformat() if self.deactivated_at else None,
            'profile_data': self.profile_data.copy(),
            'display_name': self.display_name,
            'is_deactivated': self.is_deactivated,
            'days_since_creation': self.days_since_creation,
            'has_logged_in': self.has_logged_in
        }
        
        if include_sensitive:
            user_dict['password_hash'] = self.password_hash
            
        return user_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create user entity from dictionary.
        
        Args:
            data: Dictionary containing user data
            
        Returns:
            User entity instance
        """
        # Parse datetime fields
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
            
        updated_at = None
        if data.get('updated_at'):
            updated_at = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
            
        last_login_at = None
        if data.get('last_login_at'):
            last_login_at = datetime.fromisoformat(data['last_login_at'].replace('Z', '+00:00'))
            
        deactivated_at = None
        if data.get('deactivated_at'):
            deactivated_at = datetime.fromisoformat(data['deactivated_at'].replace('Z', '+00:00'))
        
        return cls(
            id=data.get('id'),
            username=data['username'],
            email=data['email'],
            full_name=data['full_name'],
            password_hash=data.get('password_hash', ''),
            is_active=data.get('is_active', True),
            created_at=created_at,
            updated_at=updated_at,
            last_login_at=last_login_at,
            deactivated_at=deactivated_at,
            profile_data=data.get('profile_data', {})
        )

    def __str__(self) -> str:
        """String representation of user."""
        return f"User(id='{self.id}', username='{self.username}', email='{self.email}')"

    def __repr__(self) -> str:
        """Detailed string representation of user."""
        return (f"User(id='{self.id}', username='{self.username}', "
                f"email='{self.email}', full_name='{self.full_name}', "
                f"is_active={self.is_active})")