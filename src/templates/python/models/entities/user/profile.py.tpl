"""User profile model for extended user information.

This module defines the UserProfile entity which contains extended profile
information for users. This demonstrates the 4-level directory structure
and shows how to organize related entities within the same domain.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from enum import Enum


class ProfileVisibility(Enum):
    """Profile visibility levels."""
    PUBLIC = "public"
    FRIENDS = "friends"
    PRIVATE = "private"


class Gender(Enum):
    """Gender options for user profiles."""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


@dataclass
class SocialLinks:
    """Social media links for user profile."""
    twitter: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    website: Optional[str] = None
    instagram: Optional[str] = None
    facebook: Optional[str] = None

    def to_dict(self) -> Dict[str, Optional[str]]:
        """Convert to dictionary representation."""
        return {
            'twitter': self.twitter,
            'linkedin': self.linkedin,
            'github': self.github,
            'website': self.website,
            'instagram': self.instagram,
            'facebook': self.facebook
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SocialLinks':
        """Create from dictionary."""
        return cls(
            twitter=data.get('twitter'),
            linkedin=data.get('linkedin'),
            github=data.get('github'),
            website=data.get('website'),
            instagram=data.get('instagram'),
            facebook=data.get('facebook')
        )


@dataclass
class Address:
    """User address information."""
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None

    @property
    def formatted_address(self) -> str:
        """Get formatted address string."""
        parts = []
        if self.street:
            parts.append(self.street)
        if self.city:
            parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.country:
            parts.append(self.country)
        if self.postal_code:
            parts.append(self.postal_code)
        return ", ".join(parts)

    def to_dict(self) -> Dict[str, Optional[str]]:
        """Convert to dictionary representation."""
        return {
            'street': self.street,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'postal_code': self.postal_code
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Address':
        """Create from dictionary."""
        return cls(
            street=data.get('street'),
            city=data.get('city'),
            state=data.get('state'),
            country=data.get('country'),
            postal_code=data.get('postal_code')
        )


@dataclass
class UserProfile:
    """Extended user profile information.
    
    Contains additional profile information beyond the core User entity.
    This demonstrates how to separate concerns and organize related data
    within the domain model.
    
    Attributes:
        user_id: ID of the associated user
        bio: User's biography/description
        avatar_url: URL to user's profile picture
        date_of_birth: User's date of birth
        gender: User's gender
        phone: Phone number
        timezone: User's timezone
        language: Preferred language code
        visibility: Profile visibility level
        social_links: Social media links
        address: User's address information
        interests: List of user interests/hobbies
        skills: List of user skills
        occupation: User's job title/occupation
        company: User's company/organization
        education: Education information
        created_at: When profile was created
        updated_at: When profile was last updated
    """
    
    user_id: str
    
    # Basic profile information
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    phone: Optional[str] = None
    timezone: str = "UTC"
    language: str = "en"
    visibility: ProfileVisibility = ProfileVisibility.PUBLIC
    
    # Structured profile data
    social_links: SocialLinks = field(default_factory=SocialLinks)
    address: Address = field(default_factory=Address)
    
    # Lists and collections
    interests: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    
    # Professional information
    occupation: Optional[str] = None
    company: Optional[str] = None
    education: Optional[str] = None
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Post-initialization setup."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = self.created_at

    @property
    def age(self) -> Optional[int]:
        """Calculate user's age from date of birth.
        
        Returns:
            Age in years, or None if date of birth not set
        """
        if not self.date_of_birth:
            return None
        
        today = date.today()
        age = today.year - self.date_of_birth.year
        
        # Adjust if birthday hasn't occurred this year
        if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
            age -= 1
            
        return age

    @property
    def is_profile_complete(self) -> bool:
        """Check if profile has basic required information.
        
        Returns:
            True if profile is considered complete
        """
        return all([
            self.bio and len(self.bio.strip()) >= 10,
            self.avatar_url,
            self.date_of_birth,
            len(self.interests) >= 1,
            self.occupation
        ])

    @property
    def completion_percentage(self) -> int:
        """Calculate profile completion percentage.
        
        Returns:
            Completion percentage (0-100)
        """
        fields_to_check = [
            self.bio and len(self.bio.strip()) >= 10,
            self.avatar_url,
            self.date_of_birth,
            self.gender,
            self.phone,
            self.occupation,
            self.company,
            len(self.interests) >= 1,
            len(self.skills) >= 1,
            self.address.city or self.address.country,
            any([
                self.social_links.twitter,
                self.social_links.linkedin,
                self.social_links.github,
                self.social_links.website
            ])
        ]
        
        completed_fields = sum(1 for field in fields_to_check if field)
        return int((completed_fields / len(fields_to_check)) * 100)

    def add_interest(self, interest: str) -> bool:
        """Add an interest to the user's profile.
        
        Args:
            interest: Interest to add
            
        Returns:
            True if added, False if already exists
        """
        interest = interest.strip().lower()
        if interest and interest not in [i.lower() for i in self.interests]:
            self.interests.append(interest.title())
            self.updated_at = datetime.utcnow()
            return True
        return False

    def remove_interest(self, interest: str) -> bool:
        """Remove an interest from the user's profile.
        
        Args:
            interest: Interest to remove
            
        Returns:
            True if removed, False if not found
        """
        interest = interest.strip()
        for i, existing_interest in enumerate(self.interests):
            if existing_interest.lower() == interest.lower():
                del self.interests[i]
                self.updated_at = datetime.utcnow()
                return True
        return False

    def add_skill(self, skill: str) -> bool:
        """Add a skill to the user's profile.
        
        Args:
            skill: Skill to add
            
        Returns:
            True if added, False if already exists
        """
        skill = skill.strip().lower()
        if skill and skill not in [s.lower() for s in self.skills]:
            self.skills.append(skill.title())
            self.updated_at = datetime.utcnow()
            return True
        return False

    def remove_skill(self, skill: str) -> bool:
        """Remove a skill from the user's profile.
        
        Args:
            skill: Skill to remove
            
        Returns:
            True if removed, False if not found
        """
        skill = skill.strip()
        for i, existing_skill in enumerate(self.skills):
            if existing_skill.lower() == skill.lower():
                del self.skills[i]
                self.updated_at = datetime.utcnow()
                return True
        return False

    def update_social_links(self, links: Dict[str, Optional[str]]) -> None:
        """Update social media links.
        
        Args:
            links: Dictionary of social media platform names to URLs
        """
        for platform, url in links.items():
            if hasattr(self.social_links, platform):
                setattr(self.social_links, platform, url)
        self.updated_at = datetime.utcnow()

    def update_address(self, address_data: Dict[str, str]) -> None:
        """Update address information.
        
        Args:
            address_data: Dictionary containing address fields
        """
        for field, value in address_data.items():
            if hasattr(self.address, field):
                setattr(self.address, field, value)
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary representation.
        
        Returns:
            Dictionary representation of the profile
        """
        return {
            'user_id': self.user_id,
            'bio': self.bio,
            'avatar_url': self.avatar_url,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'gender': self.gender.value if self.gender else None,
            'phone': self.phone,
            'timezone': self.timezone,
            'language': self.language,
            'visibility': self.visibility.value,
            'social_links': self.social_links.to_dict(),
            'address': self.address.to_dict(),
            'interests': self.interests.copy(),
            'skills': self.skills.copy(),
            'occupation': self.occupation,
            'company': self.company,
            'education': self.education,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'age': self.age,
            'is_profile_complete': self.is_profile_complete,
            'completion_percentage': self.completion_percentage
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfile':
        """Create profile from dictionary.
        
        Args:
            data: Dictionary containing profile data
            
        Returns:
            UserProfile instance
        """
        # Parse date fields
        date_of_birth = None
        if data.get('date_of_birth'):
            date_of_birth = date.fromisoformat(data['date_of_birth'])
            
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
            
        updated_at = None
        if data.get('updated_at'):
            updated_at = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
        
        # Parse enum fields
        gender = None
        if data.get('gender'):
            gender = Gender(data['gender'])
            
        visibility = ProfileVisibility.PUBLIC
        if data.get('visibility'):
            visibility = ProfileVisibility(data['visibility'])
        
        # Parse structured fields
        social_links = SocialLinks()
        if data.get('social_links'):
            social_links = SocialLinks.from_dict(data['social_links'])
            
        address = Address()
        if data.get('address'):
            address = Address.from_dict(data['address'])
        
        return cls(
            user_id=data['user_id'],
            bio=data.get('bio'),
            avatar_url=data.get('avatar_url'),
            date_of_birth=date_of_birth,
            gender=gender,
            phone=data.get('phone'),
            timezone=data.get('timezone', 'UTC'),
            language=data.get('language', 'en'),
            visibility=visibility,
            social_links=social_links,
            address=address,
            interests=data.get('interests', []),
            skills=data.get('skills', []),
            occupation=data.get('occupation'),
            company=data.get('company'),
            education=data.get('education'),
            created_at=created_at,
            updated_at=updated_at
        )

    def __str__(self) -> str:
        """String representation of profile."""
        return f"UserProfile(user_id='{self.user_id}', completion={self.completion_percentage}%)"

    def __repr__(self) -> str:
        """Detailed string representation of profile."""
        return (f"UserProfile(user_id='{self.user_id}', bio='{self.bio[:50] if self.bio else None}...', "
                f"completion={self.completion_percentage}%)")