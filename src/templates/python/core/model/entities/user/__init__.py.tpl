"""User domain entities.

This module contains all entities related to the user domain,
demonstrating the 4-level directory structure for organizing
related domain models.
"""

from .user import User
from .profile import UserProfile, ProfileVisibility, Gender, SocialLinks, Address

__all__ = [
    "User",
    "UserProfile",
    "ProfileVisibility",
    "Gender", 
    "SocialLinks",
    "Address",
]