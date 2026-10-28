"""User validation logic.

This module contains validation functions and classes specific to user
entities and operations. It provides reusable validation logic that can
be used across different layers of the application.
"""

import re
from typing import List, Optional, Dict, Any
from datetime import datetime

from models.entities.user.user import User
from core.services.exceptions import ValidationError


class UserValidator:
    """Validator class for user-related operations.
    
    Provides validation methods for user data, business rules,
    and domain-specific constraints.
    """

    # Email regex pattern (basic validation)
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    # Username pattern (alphanumeric + underscore, dash)
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')

    @classmethod
    def validate_email(cls, email: str) -> None:
        """Validate email address format.
        
        Args:
            email: Email address to validate
            
        Raises:
            ValidationError: If email format is invalid
        """
        if not email:
            raise ValidationError("Email address is required")
        
        if len(email) > 254:  # RFC 5321 limit
            raise ValidationError("Email address is too long")
            
        if not cls.EMAIL_PATTERN.match(email):
            raise ValidationError("Invalid email address format")
        
        # Check for consecutive dots
        if '..' in email:
            raise ValidationError("Email address cannot contain consecutive dots")

    @classmethod
    def validate_username(cls, username: str) -> None:
        """Validate username format and constraints.
        
        Args:
            username: Username to validate
            
        Raises:
            ValidationError: If username is invalid
        """
        if not username:
            raise ValidationError("Username is required")
        
        username = username.strip()
        
        if len(username) < 3:
            raise ValidationError("Username must be at least 3 characters long")
        
        if len(username) > 50:
            raise ValidationError("Username must be at most 50 characters long")
        
        if not cls.USERNAME_PATTERN.match(username):
            raise ValidationError("Username can only contain letters, numbers, underscores, and dashes")
        
        # Check for reserved usernames
        reserved_usernames = {
            'admin', 'administrator', 'root', 'system', 'api', 'www',
            'mail', 'ftp', 'support', 'help', 'info', 'service',
            'test', 'demo', 'null', 'undefined'
        }
        
        if username.lower() in reserved_usernames:
            raise ValidationError("This username is reserved and cannot be used")

    @classmethod
    def validate_password(cls, password: str) -> None:
        """Validate password strength and format.
        
        Args:
            password: Password to validate
            
        Raises:
            ValidationError: If password doesn't meet requirements
        """
        if not password:
            raise ValidationError("Password is required")
        
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long")
        
        if len(password) > 128:
            raise ValidationError("Password is too long (maximum 128 characters)")
        
        # Check for at least one uppercase letter
        if not any(c.isupper() for c in password):
            raise ValidationError("Password must contain at least one uppercase letter")
        
        # Check for at least one lowercase letter
        if not any(c.islower() for c in password):
            raise ValidationError("Password must contain at least one lowercase letter")
        
        # Check for at least one digit
        if not any(c.isdigit() for c in password):
            raise ValidationError("Password must contain at least one digit")
        
        # Check for at least one special character
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            raise ValidationError("Password must contain at least one special character")
        
        # Check for common weak passwords
        weak_passwords = {
            'password', 'password123', '12345678', 'qwerty',
            'abc123', 'admin123', 'letmein', 'welcome',
            'monkey', 'dragon', 'princess', 'shadow'
        }
        
        if password.lower() in weak_passwords:
            raise ValidationError("This password is too common and weak")

    @classmethod
    def validate_full_name(cls, full_name: str) -> None:
        """Validate user's full name.
        
        Args:
            full_name: Full name to validate
            
        Raises:
            ValidationError: If full name is invalid
        """
        if not full_name:
            raise ValidationError("Full name is required")
        
        full_name = full_name.strip()
        
        if len(full_name) < 2:
            raise ValidationError("Full name must be at least 2 characters long")
        
        if len(full_name) > 100:
            raise ValidationError("Full name must be at most 100 characters long")
        
        # Check for valid characters (letters, spaces, apostrophes, hyphens)
        name_pattern = re.compile(r"^[a-zA-Z\s'\-\.]+$")
        if not name_pattern.match(full_name):
            raise ValidationError("Full name can only contain letters, spaces, apostrophes, hyphens, and dots")
        
        # Check for excessive spaces
        if '  ' in full_name:
            raise ValidationError("Full name cannot contain multiple consecutive spaces")

    @classmethod
    def validate_profile_data(cls, profile_data: Optional[Dict[str, Any]]) -> None:
        """Validate user profile data structure.
        
        Args:
            profile_data: Profile data dictionary to validate
            
        Raises:
            ValidationError: If profile data is invalid
        """
        if profile_data is None:
            return
        
        if not isinstance(profile_data, dict):
            raise ValidationError("Profile data must be a dictionary")
        
        # Validate allowed fields and their types
        allowed_fields = {
            'bio': str,
            'location': str,
            'website': str,
            'phone': str,
            'date_of_birth': str,  # ISO format string
            'timezone': str,
            'language': str,
            'avatar_url': str
        }
        
        for field, value in profile_data.items():
            if field not in allowed_fields:
                raise ValidationError(f"Unknown profile field: {field}")
            
            expected_type = allowed_fields[field]
            if not isinstance(value, expected_type):
                raise ValidationError(f"Profile field '{field}' must be of type {expected_type.__name__}")
            
            # Validate specific fields
            if field == 'bio' and len(value) > 500:
                raise ValidationError("Bio must be at most 500 characters long")
            
            elif field == 'website' and value:
                cls._validate_url(value, "Website URL")
            
            elif field == 'avatar_url' and value:
                cls._validate_url(value, "Avatar URL")
            
            elif field == 'phone' and value:
                cls._validate_phone_number(value)
            
            elif field == 'date_of_birth' and value:
                cls._validate_date_of_birth(value)

    @classmethod
    def validate_user_entity(cls, user: User) -> None:
        """Validate complete user entity.
        
        Args:
            user: User entity to validate
            
        Raises:
            ValidationError: If user entity is invalid
        """
        # Validate required fields
        cls.validate_username(user.username)
        cls.validate_email(user.email)
        cls.validate_full_name(user.full_name)
        
        # Validate optional fields
        if user.profile_data:
            cls.validate_profile_data(user.profile_data)
        
        # Validate business rules
        if user.deactivated_at and user.is_active:
            raise ValidationError("User cannot be active if it has a deactivation date")
        
        if user.last_login_at and user.created_at and user.last_login_at < user.created_at:
            raise ValidationError("Last login date cannot be before creation date")

    @classmethod
    def _validate_url(cls, url: str, field_name: str) -> None:
        """Validate URL format."""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(url):
            raise ValidationError(f"{field_name} must be a valid URL")
        
        if len(url) > 2048:
            raise ValidationError(f"{field_name} is too long")

    @classmethod
    def _validate_phone_number(cls, phone: str) -> None:
        """Validate phone number format."""
        # Simple phone number validation (international format)
        phone_pattern = re.compile(r'^\+?[1-9]\d{1,14}$')
        
        # Remove common separators for validation
        clean_phone = re.sub(r'[\s\-\(\)\.]+', '', phone)
        
        if not phone_pattern.match(clean_phone):
            raise ValidationError("Phone number must be in international format")

    @classmethod
    def _validate_date_of_birth(cls, date_str: str) -> None:
        """Validate date of birth."""
        try:
            # Try to parse ISO format date
            birth_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            
            # Check if date is reasonable (not in future, not too old)
            now = datetime.utcnow()
            if birth_date.date() > now.date():
                raise ValidationError("Date of birth cannot be in the future")
            
            age_years = (now - birth_date).days / 365.25
            if age_years > 150:
                raise ValidationError("Date of birth is too far in the past")
            
            if age_years < 13:
                raise ValidationError("Users must be at least 13 years old")
                
        except ValueError:
            raise ValidationError("Date of birth must be in ISO format (YYYY-MM-DD)")


def validate_user_creation_data(data: Dict[str, Any]) -> List[str]:
    """Validate data for user creation and return list of validation errors.
    
    Args:
        data: User creation data dictionary
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    try:
        UserValidator.validate_username(data.get('username', ''))
    except ValidationError as e:
        errors.append(str(e))
    
    try:
        UserValidator.validate_email(data.get('email', ''))
    except ValidationError as e:
        errors.append(str(e))
    
    try:
        UserValidator.validate_full_name(data.get('full_name', ''))
    except ValidationError as e:
        errors.append(str(e))
    
    try:
        UserValidator.validate_password(data.get('password', ''))
    except ValidationError as e:
        errors.append(str(e))
    
    try:
        UserValidator.validate_profile_data(data.get('profile_data'))
    except ValidationError as e:
        errors.append(str(e))
    
    return errors