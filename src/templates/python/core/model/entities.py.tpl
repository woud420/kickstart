"""Domain entities for {{service_name}} service.

Domain entities represent the core business objects with their properties
and behaviors. These are pure Python classes with minimal dependencies.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import uuid4


@dataclass
class User:
    """User entity representing a user in the system."""
    
    id: str = field(default_factory=lambda: str(uuid4()))
    username: str = ""
    email: str = ""
    full_name: str = ""
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None
    profile_data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization validation."""
        if not self.username:
            raise ValueError("Username is required")
        if not self.email:
            raise ValueError("Email is required")
        if "@" not in self.email:
            raise ValueError("Invalid email format")
    
    def update_last_login(self) -> None:
        """Update the last login timestamp."""
        self.last_login_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """Deactivate the user."""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """Activate the user."""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def update_profile(self, profile_data: Dict[str, Any]) -> None:
        """Update user profile data."""
        self.profile_data.update(profile_data)
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary representation."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "profile_data": self.profile_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """Create user from dictionary representation."""
        # Parse datetime fields
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        
        updated_at = None
        if data.get("updated_at"):
            updated_at = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
        
        last_login_at = None
        if data.get("last_login_at"):
            last_login_at = datetime.fromisoformat(data["last_login_at"].replace("Z", "+00:00"))
        
        return cls(
            id=data.get("id", str(uuid4())),
            username=data.get("username", ""),
            email=data.get("email", ""),
            full_name=data.get("full_name", ""),
            is_active=data.get("is_active", True),
            created_at=created_at or datetime.utcnow(),
            updated_at=updated_at or datetime.utcnow(),
            last_login_at=last_login_at,
            profile_data=data.get("profile_data", {})
        )


@dataclass
class UserProfile:
    """User profile entity for extended user information."""
    
    user_id: str
    bio: str = ""
    avatar_url: str = ""
    location: str = ""
    website: str = ""
    social_links: Dict[str, str] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Post-initialization validation."""
        if not self.user_id:
            raise ValueError("User ID is required")
    
    def update_social_links(self, links: Dict[str, str]) -> None:
        """Update social media links."""
        self.social_links.update(links)
        self.updated_at = datetime.utcnow()
    
    def update_preferences(self, preferences: Dict[str, Any]) -> None:
        """Update user preferences."""
        self.preferences.update(preferences)
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary representation."""
        return {
            "user_id": self.user_id,
            "bio": self.bio,
            "avatar_url": self.avatar_url,
            "location": self.location,
            "website": self.website,
            "social_links": self.social_links,
            "preferences": self.preferences,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserProfile":
        """Create profile from dictionary representation."""
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        
        updated_at = None
        if data.get("updated_at"):
            updated_at = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
        
        return cls(
            user_id=data["user_id"],
            bio=data.get("bio", ""),
            avatar_url=data.get("avatar_url", ""),
            location=data.get("location", ""),
            website=data.get("website", ""),
            social_links=data.get("social_links", {}),
            preferences=data.get("preferences", {}),
            created_at=created_at or datetime.utcnow(),
            updated_at=updated_at or datetime.utcnow()
        )