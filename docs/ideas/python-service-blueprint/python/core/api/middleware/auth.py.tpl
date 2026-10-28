"""Authentication middleware for API requests.

This module provides authentication middleware to validate and extract
user information from requests. It supports JWT token-based authentication
and integrates with the FastAPI dependency injection system.
"""

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import jwt
import logging
from datetime import datetime, timedelta

from core.services.user_service import UserService
from core.services.exceptions import NotFoundError, ServiceError
from models.dto.responses import UserResponse
from config.settings import get_settings

logger = logging.getLogger(__name__)

# Security scheme for JWT tokens
security = HTTPBearer()
settings = get_settings()


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class AuthorizationError(Exception):
    """Raised when authorization fails."""
    pass


def create_access_token(user_id: str, username: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token for a user.
    
    Args:
        user_id: User ID to encode in token
        username: Username to encode in token
        expires_delta: Token expiration time (defaults to configured value)
        
    Returns:
        Encoded JWT token string
    """
    try:
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        
        to_encode = {
            "sub": user_id,
            "username": username,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.secret_key, 
            algorithm=settings.algorithm
        )
        
        logger.info(f"Access token created for user {user_id}")
        return encoded_jwt
        
    except Exception as e:
        logger.error(f"Failed to create access token: {e}")
        raise AuthenticationError("Failed to create access token")


def create_refresh_token(user_id: str, username: str) -> str:
    """Create a JWT refresh token for a user.
    
    Args:
        user_id: User ID to encode in token
        username: Username to encode in token
        
    Returns:
        Encoded JWT refresh token string
    """
    try:
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
        
        to_encode = {
            "sub": user_id,
            "username": username,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm
        )
        
        logger.info(f"Refresh token created for user {user_id}")
        return encoded_jwt
        
    except Exception as e:
        logger.error(f"Failed to create refresh token: {e}")
        raise AuthenticationError("Failed to create refresh token")


def verify_token(token: str, token_type: str = "access") -> dict:
    """Verify and decode a JWT token.
    
    Args:
        token: JWT token to verify
        token_type: Expected token type ("access" or "refresh")
        
    Returns:
        Decoded token payload
        
    Raises:
        AuthenticationError: If token is invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        
        # Verify token type
        if payload.get("type") != token_type:
            raise AuthenticationError(f"Invalid token type, expected {token_type}")
        
        # Verify expiration
        exp = payload.get("exp")
        if exp is None or datetime.fromtimestamp(exp) < datetime.utcnow():
            raise AuthenticationError("Token has expired")
        
        # Extract user information
        user_id = payload.get("sub")
        username = payload.get("username")
        
        if not user_id or not username:
            raise AuthenticationError("Invalid token payload")
        
        return {
            "user_id": user_id,
            "username": username,
            "exp": exp,
            "iat": payload.get("iat")
        }
        
    except jwt.PyJWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise AuthenticationError("Invalid token")
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise AuthenticationError("Token verification failed")


async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_service: UserService = Depends(lambda: None)  # Will be properly injected
) -> UserResponse:
    """Extract and validate current user from JWT token.
    
    Args:
        credentials: HTTP authorization credentials
        user_service: User service for user lookup
        
    Returns:
        Current user response data
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        token = credentials.credentials
        
        # Verify token and extract user info
        token_data = verify_token(token, "access")
        user_id = token_data["user_id"]
        
        # Get user from database
        if user_service is None:
            # This should be properly injected in the actual implementation
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User service not available"
            )
        
        user_response = await user_service.get_user(user_id)
        
        # Check if user is active
        if not user_response.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is deactivated"
            )
        
        logger.debug(f"Authenticated user: {user_id}")
        return user_response
        
    except AuthenticationError as e:
        logger.warning(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except NotFoundError:
        logger.warning(f"User not found during authentication: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except ServiceError as e:
        logger.error(f"Service error during authentication: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    user_service: UserService = Depends(lambda: None)  # Will be properly injected
) -> Optional[UserResponse]:
    """Extract current user from token if provided, otherwise return None.
    
    Used for endpoints that can work with or without authentication.
    
    Args:
        credentials: Optional HTTP authorization credentials
        user_service: User service for user lookup
        
    Returns:
        Current user response data if authenticated, None otherwise
    """
    try:
        if credentials is None:
            return None
        
        return await get_current_user_from_token(credentials, user_service)
        
    except HTTPException:
        # Return None for optional authentication
        return None


def require_active_user(current_user: UserResponse = Depends(get_current_user_from_token)) -> UserResponse:
    """Require an active authenticated user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Active user response
        
    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    return current_user


def require_user_roles(allowed_roles: list[str]):
    """Create a dependency that requires specific user roles.
    
    Args:
        allowed_roles: List of roles that are allowed access
        
    Returns:
        Dependency function that checks user roles
    """
    def check_roles(current_user: UserResponse = Depends(get_current_user_from_token)) -> UserResponse:
        # In a real application, user roles would be stored and checked here
        # For now, we'll assume all authenticated users have basic access
        user_roles = current_user.profile_data.get("roles", ["user"])
        
        if not any(role in allowed_roles for role in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return current_user
    
    return check_roles


# Convenience dependencies for common role checks
require_admin = require_user_roles(["admin"])
require_moderator = require_user_roles(["admin", "moderator"])


class RateLimitError(Exception):
    """Raised when rate limit is exceeded."""
    pass


def create_rate_limiter(max_requests: int, window_seconds: int):
    """Create a rate limiting dependency.
    
    Args:
        max_requests: Maximum requests allowed in the window
        window_seconds: Time window in seconds
        
    Returns:
        Rate limiting dependency function
    """
    # In a real application, this would use Redis or another store
    # to track request rates across multiple server instances
    request_counts = {}
    
    def rate_limit(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
    ):
        # For demo purposes, we'll track by IP or user
        # In production, use a proper rate limiting solution
        import time
        
        current_time = time.time()
        window_start = current_time - window_seconds
        
        # Simple in-memory rate limiting (not production ready)
        identifier = "anonymous"
        if credentials:
            try:
                token_data = verify_token(credentials.credentials)
                identifier = token_data["user_id"]
            except AuthenticationError:
                pass
        
        # Clean old entries
        if identifier in request_counts:
            request_counts[identifier] = [
                timestamp for timestamp in request_counts[identifier]
                if timestamp > window_start
            ]
        else:
            request_counts[identifier] = []
        
        # Check rate limit
        if len(request_counts[identifier]) >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {max_requests} requests per {window_seconds} seconds"
            )
        
        # Record this request
        request_counts[identifier].append(current_time)
    
    return rate_limit


# Common rate limiters
rate_limit_strict = create_rate_limiter(10, 60)  # 10 requests per minute
rate_limit_normal = create_rate_limiter(100, 60)  # 100 requests per minute
rate_limit_generous = create_rate_limiter(1000, 60)  # 1000 requests per minute