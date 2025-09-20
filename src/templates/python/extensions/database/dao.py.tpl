"""Database Data Access Objects (DAOs) - PostgreSQL implementation.

This module provides PostgreSQL-specific implementations of the repository interfaces.
"""

import asyncpg
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..model.entities import User, UserProfile
from ..model.dto import PaginationRequest
from ..model.repository import (
    UserRepository, UserProfileRepository,
    UserNotFoundError, UserAlreadyExistsError,
    ProfileNotFoundError, ProfileAlreadyExistsError
)


class PostgreSQLUserRepository(UserRepository):
    """PostgreSQL implementation of UserRepository."""
    
    def __init__(self, connection_pool: asyncpg.Pool):
        """Initialize the PostgreSQL user repository.
        
        Args:
            connection_pool: asyncpg connection pool
        """
        self.pool = connection_pool
    
    async def create(self, user: User) -> User:
        """Create a new user in PostgreSQL."""
        query = """
            INSERT INTO users (id, username, email, full_name, is_active, created_at, updated_at, profile_data)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id, username, email, full_name, is_active, created_at, updated_at, last_login_at, profile_data
        """
        
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow(
                    query,
                    user.id,
                    user.username,
                    user.email,
                    user.full_name,
                    user.is_active,
                    user.created_at,
                    user.updated_at,
                    user.profile_data
                )
                
                return User(
                    id=row['id'],
                    username=row['username'],
                    email=row['email'],
                    full_name=row['full_name'],
                    is_active=row['is_active'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    last_login_at=row['last_login_at'],
                    profile_data=row['profile_data'] or {}
                )
            
            except asyncpg.UniqueViolationError as e:
                if 'username' in str(e):
                    raise UserAlreadyExistsError(f"User with username '{user.username}' already exists")
                elif 'email' in str(e):
                    raise UserAlreadyExistsError(f"User with email '{user.email}' already exists")
                else:
                    raise UserAlreadyExistsError(f"User with ID '{user.id}' already exists")
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID from PostgreSQL."""
        query = """
            SELECT id, username, email, full_name, is_active, created_at, updated_at, last_login_at, profile_data
            FROM users
            WHERE id = $1
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id)
            
            if not row:
                return None
            
            return User(
                id=row['id'],
                username=row['username'],
                email=row['email'],
                full_name=row['full_name'],
                is_active=row['is_active'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                last_login_at=row['last_login_at'],
                profile_data=row['profile_data'] or {}
            )
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username from PostgreSQL."""
        query = """
            SELECT id, username, email, full_name, is_active, created_at, updated_at, last_login_at, profile_data
            FROM users
            WHERE username = $1
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, username)
            
            if not row:
                return None
            
            return User(
                id=row['id'],
                username=row['username'],
                email=row['email'],
                full_name=row['full_name'],
                is_active=row['is_active'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                last_login_at=row['last_login_at'],
                profile_data=row['profile_data'] or {}
            )
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email from PostgreSQL."""
        query = """
            SELECT id, username, email, full_name, is_active, created_at, updated_at, last_login_at, profile_data
            FROM users
            WHERE email = $1
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, email)
            
            if not row:
                return None
            
            return User(
                id=row['id'],
                username=row['username'],
                email=row['email'],
                full_name=row['full_name'],
                is_active=row['is_active'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                last_login_at=row['last_login_at'],
                profile_data=row['profile_data'] or {}
            )
    
    async def list_users(self, pagination: PaginationRequest) -> tuple[List[User], int]:
        """List users with pagination from PostgreSQL."""
        # Build ORDER BY clause
        order_direction = "ASC" if pagination.sort_order == "asc" else "DESC"
        order_by = f"ORDER BY {pagination.sort_by} {order_direction}"
        
        # Count query
        count_query = "SELECT COUNT(*) FROM users"
        
        # Data query with pagination
        data_query = f"""
            SELECT id, username, email, full_name, is_active, created_at, updated_at, last_login_at, profile_data
            FROM users
            {order_by}
            LIMIT $1 OFFSET $2
        """
        
        async with self.pool.acquire() as conn:
            # Get total count
            total = await conn.fetchval(count_query)
            
            # Get paginated data
            rows = await conn.fetch(data_query, pagination.page_size, pagination.offset)
            
            users = [
                User(
                    id=row['id'],
                    username=row['username'],
                    email=row['email'],
                    full_name=row['full_name'],
                    is_active=row['is_active'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    last_login_at=row['last_login_at'],
                    profile_data=row['profile_data'] or {}
                )
                for row in rows
            ]
            
            return users, total
    
    async def update(self, user: User) -> User:
        """Update user in PostgreSQL."""
        query = """
            UPDATE users
            SET username = $2, email = $3, full_name = $4, is_active = $5, updated_at = $6, 
                last_login_at = $7, profile_data = $8
            WHERE id = $1
            RETURNING id, username, email, full_name, is_active, created_at, updated_at, last_login_at, profile_data
        """
        
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow(
                    query,
                    user.id,
                    user.username,
                    user.email,
                    user.full_name,
                    user.is_active,
                    user.updated_at,
                    user.last_login_at,
                    user.profile_data
                )
                
                if not row:
                    raise UserNotFoundError(f"User with ID '{user.id}' not found")
                
                return User(
                    id=row['id'],
                    username=row['username'],
                    email=row['email'],
                    full_name=row['full_name'],
                    is_active=row['is_active'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    last_login_at=row['last_login_at'],
                    profile_data=row['profile_data'] or {}
                )
            
            except asyncpg.UniqueViolationError as e:
                if 'username' in str(e):
                    raise UserAlreadyExistsError(f"User with username '{user.username}' already exists")
                elif 'email' in str(e):
                    raise UserAlreadyExistsError(f"User with email '{user.email}' already exists")
                else:
                    raise
    
    async def delete(self, user_id: str) -> bool:
        """Delete user from PostgreSQL."""
        query = "DELETE FROM users WHERE id = $1"
        
        async with self.pool.acquire() as conn:
            result = await conn.execute(query, user_id)
            return result.split()[-1] == "1"  # Check if one row was deleted
    
    async def exists_by_username(self, username: str) -> bool:
        """Check if user exists by username in PostgreSQL."""
        query = "SELECT EXISTS(SELECT 1 FROM users WHERE username = $1)"
        
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, username)
    
    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email in PostgreSQL."""
        query = "SELECT EXISTS(SELECT 1 FROM users WHERE email = $1)"
        
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, email)


class PostgreSQLUserProfileRepository(UserProfileRepository):
    """PostgreSQL implementation of UserProfileRepository."""
    
    def __init__(self, connection_pool: asyncpg.Pool):
        """Initialize the PostgreSQL user profile repository.
        
        Args:
            connection_pool: asyncpg connection pool
        """
        self.pool = connection_pool
    
    async def create(self, profile: UserProfile) -> UserProfile:
        """Create a new profile in PostgreSQL."""
        query = """
            INSERT INTO user_profiles (user_id, bio, avatar_url, location, website, social_links, preferences, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING user_id, bio, avatar_url, location, website, social_links, preferences, created_at, updated_at
        """
        
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow(
                    query,
                    profile.user_id,
                    profile.bio,
                    profile.avatar_url,
                    profile.location,
                    profile.website,
                    profile.social_links,
                    profile.preferences,
                    profile.created_at,
                    profile.updated_at
                )
                
                return UserProfile(
                    user_id=row['user_id'],
                    bio=row['bio'],
                    avatar_url=row['avatar_url'],
                    location=row['location'],
                    website=row['website'],
                    social_links=row['social_links'] or {},
                    preferences=row['preferences'] or {},
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
            
            except asyncpg.UniqueViolationError:
                raise ProfileAlreadyExistsError(f"Profile for user '{profile.user_id}' already exists")
            except asyncpg.ForeignKeyViolationError:
                raise UserNotFoundError(f"User with ID '{profile.user_id}' not found")
    
    async def get_by_user_id(self, user_id: str) -> Optional[UserProfile]:
        """Get profile by user ID from PostgreSQL."""
        query = """
            SELECT user_id, bio, avatar_url, location, website, social_links, preferences, created_at, updated_at
            FROM user_profiles
            WHERE user_id = $1
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id)
            
            if not row:
                return None
            
            return UserProfile(
                user_id=row['user_id'],
                bio=row['bio'],
                avatar_url=row['avatar_url'],
                location=row['location'],
                website=row['website'],
                social_links=row['social_links'] or {},
                preferences=row['preferences'] or {},
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
    
    async def update(self, profile: UserProfile) -> UserProfile:
        """Update profile in PostgreSQL."""
        query = """
            UPDATE user_profiles
            SET bio = $2, avatar_url = $3, location = $4, website = $5, 
                social_links = $6, preferences = $7, updated_at = $8
            WHERE user_id = $1
            RETURNING user_id, bio, avatar_url, location, website, social_links, preferences, created_at, updated_at
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                profile.user_id,
                profile.bio,
                profile.avatar_url,
                profile.location,
                profile.website,
                profile.social_links,
                profile.preferences,
                profile.updated_at
            )
            
            if not row:
                raise ProfileNotFoundError(f"Profile for user '{profile.user_id}' not found")
            
            return UserProfile(
                user_id=row['user_id'],
                bio=row['bio'],
                avatar_url=row['avatar_url'],
                location=row['location'],
                website=row['website'],
                social_links=row['social_links'] or {},
                preferences=row['preferences'] or {},
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
    
    async def delete(self, user_id: str) -> bool:
        """Delete profile from PostgreSQL."""
        query = "DELETE FROM user_profiles WHERE user_id = $1"
        
        async with self.pool.acquire() as conn:
            result = await conn.execute(query, user_id)
            return result.split()[-1] == "1"  # Check if one row was deleted