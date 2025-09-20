"""JWT Authentication extension for {{service_name}}.

This module provides JWT-based authentication functionality as an extension.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union

from jose import JWTError, jwt
from passlib.context import CryptContext

logger = logging.getLogger(__name__)


class JWTAuth:
    """JWT authentication handler."""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256",
                 access_token_expire_minutes: int = 30,
                 refresh_token_expire_days: int = 7):
        """Initialize JWT authentication.
        
        Args:
            secret_key: Secret key for JWT signing
            algorithm: JWT algorithm (default: HS256)
            access_token_expire_minutes: Access token expiration in minutes
            refresh_token_expire_days: Refresh token expiration in days
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        
        # Password hashing context
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def create_access_token(self, data: Dict[str, Any], 
                          expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token.
        
        Args:
            data: Data to encode in token
            expires_delta: Custom expiration time
            
        Returns:
            JWT access token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        logger.debug(f"Created access token for user: {data.get('sub')}")
        
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any],
                           expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT refresh token.
        
        Args:
            data: Data to encode in token
            expires_delta: Custom expiration time
            
        Returns:
            JWT refresh token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        logger.debug(f"Created refresh token for user: {data.get('sub')}")
        
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token.
        
        Args:
            token: JWT token to verify
            token_type: Expected token type (access or refresh)
            
        Returns:
            Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check token type
            if payload.get("type") != token_type:
                logger.warning(f"Invalid token type: expected {token_type}, got {payload.get('type')}")
                return None
            
            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                logger.debug("Token has expired")
                return None
            
            logger.debug(f"Verified {token_type} token for user: {payload.get('sub')}")
            return payload
            
        except JWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Create new access token from refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New access token or None if refresh token is invalid
        """
        payload = self.verify_token(refresh_token, "refresh")
        if not payload:
            return None
        
        # Create new access token with same user data
        access_data = {
            "sub": payload.get("sub"),
            "username": payload.get("username"),
            "email": payload.get("email")
        }
        
        return self.create_access_token(access_data)
    
    def hash_password(self, password: str) -> str:
        """Hash a password.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        hashed = self.pwd_context.hash(password)
        logger.debug("Password hashed successfully")
        return hashed
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            True if password matches
        """
        verified = self.pwd_context.verify(plain_password, hashed_password)
        logger.debug(f"Password verification: {'success' if verified else 'failed'}")
        return verified


class AuthenticationError(Exception):
    """Authentication related errors."""
    pass


class InvalidTokenError(AuthenticationError):
    """Invalid token error."""
    pass


class ExpiredTokenError(AuthenticationError):
    """Expired token error."""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Invalid credentials error."""
    pass


# Authentication middleware
class AuthMiddleware:
    """Authentication middleware for request validation."""
    
    def __init__(self, jwt_auth: JWTAuth):
        """Initialize auth middleware.
        
        Args:
            jwt_auth: JWT authentication handler
        """
        self.jwt_auth = jwt_auth
    
    def extract_token_from_header(self, authorization: str) -> Optional[str]:
        """Extract token from Authorization header.
        
        Args:
            authorization: Authorization header value
            
        Returns:
            JWT token or None
        """
        if not authorization:
            return None
        
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
        
        return parts[1]
    
    def authenticate_request(self, authorization: str) -> Optional[Dict[str, Any]]:
        """Authenticate request using Authorization header.
        
        Args:
            authorization: Authorization header value
            
        Returns:
            User data from token or None if authentication fails
        """
        token = self.extract_token_from_header(authorization)
        if not token:
            return None
        
        payload = self.jwt_auth.verify_token(token, "access")
        if not payload:
            return None
        
        return {
            "user_id": payload.get("sub"),
            "username": payload.get("username"),
            "email": payload.get("email")
        }
    
    def require_auth(self, authorization: str) -> Dict[str, Any]:
        """Require authentication for request.
        
        Args:
            authorization: Authorization header value
            
        Returns:
            User data from token
            
        Raises:
            InvalidTokenError: If token is invalid or missing
        """
        user_data = self.authenticate_request(authorization)
        if not user_data:
            raise InvalidTokenError("Invalid or missing authentication token")
        
        return user_data


# Authentication service
class AuthService:
    """Authentication service with user management."""
    
    def __init__(self, jwt_auth: JWTAuth, user_repository):
        """Initialize auth service.
        
        Args:
            jwt_auth: JWT authentication handler
            user_repository: User repository for user operations
        """
        self.jwt_auth = jwt_auth
        self.user_repo = user_repository
    
    async def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with username/password.
        
        Args:
            username: Username or email
            password: Plain text password
            
        Returns:
            User data if authentication successful, None otherwise
        """
        try:
            # Try to find user by username or email
            user = await self.user_repo.get_by_username(username)
            if not user:
                user = await self.user_repo.get_by_email(username)
            
            if not user:
                logger.debug(f"User not found: {username}")
                return None
            
            # Check if user is active
            if not user.is_active:
                logger.debug(f"User is not active: {username}")
                return None
            
            # For this example, we'll assume password is stored in profile_data
            # In a real implementation, you'd have a separate password field
            stored_password = user.profile_data.get("password_hash")
            if not stored_password:
                logger.debug(f"No password set for user: {username}")
                return None
            
            # Verify password
            if not self.jwt_auth.verify_password(password, stored_password):
                logger.debug(f"Invalid password for user: {username}")
                return None
            
            # Update last login
            user.update_last_login()
            await self.user_repo.update(user)
            
            logger.info(f"User authenticated successfully: {username}")
            return {
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name
            }
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    async def login(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Login user and create tokens.
        
        Args:
            username: Username or email
            password: Plain text password
            
        Returns:
            Login response with tokens or None if login failed
        """
        user_data = await self.authenticate_user(username, password)
        if not user_data:
            return None
        
        # Create tokens
        token_data = {
            "sub": user_data["user_id"],
            "username": user_data["username"],
            "email": user_data["email"]
        }
        
        access_token = self.jwt_auth.create_access_token(token_data)
        refresh_token = self.jwt_auth.create_refresh_token(token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.jwt_auth.access_token_expire_minutes * 60,
            "user": user_data
        }
    
    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh access token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New token response or None if refresh failed
        """
        new_access_token = self.jwt_auth.refresh_access_token(refresh_token)
        if not new_access_token:
            return None
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": self.jwt_auth.access_token_expire_minutes * 60
        }
    
    async def register_user(self, username: str, email: str, password: str,
                          full_name: str = "") -> Optional[Dict[str, Any]]:
        """Register new user with password.
        
        Args:
            username: Username
            email: Email address
            password: Plain text password
            full_name: Full name (optional)
            
        Returns:
            Registration response or None if registration failed
        """
        try:
            from ..model.entities import User
            
            # Hash password
            password_hash = self.jwt_auth.hash_password(password)
            
            # Create user with password in profile_data
            user = User(
                username=username,
                email=email,
                full_name=full_name,
                profile_data={"password_hash": password_hash}
            )
            
            # Save user
            created_user = await self.user_repo.create(user)
            
            logger.info(f"User registered successfully: {username}")
            
            # Return user data (without password)
            return {
                "user_id": created_user.id,
                "username": created_user.username,
                "email": created_user.email,
                "full_name": created_user.full_name,
                "created_at": created_user.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return None


# Global auth instances
_jwt_auth: Optional[JWTAuth] = None
_auth_middleware: Optional[AuthMiddleware] = None


def get_jwt_auth() -> JWTAuth:
    """Get global JWT auth instance.
    
    Returns:
        JWT auth instance
    """
    global _jwt_auth
    if _jwt_auth is None:
        import os
        _jwt_auth = JWTAuth(
            secret_key=os.environ.get("SECRET_KEY", "your-secret-key-change-in-production"),
            access_token_expire_minutes=int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
            refresh_token_expire_days=int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        )
    return _jwt_auth


def get_auth_middleware() -> AuthMiddleware:
    """Get global auth middleware instance.
    
    Returns:
        Auth middleware instance
    """
    global _auth_middleware
    if _auth_middleware is None:
        _auth_middleware = AuthMiddleware(get_jwt_auth())
    return _auth_middleware