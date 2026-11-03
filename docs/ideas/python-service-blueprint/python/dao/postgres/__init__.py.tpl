"""PostgreSQL Data Access Objects.

This module contains PostgreSQL-specific implementations of DAO classes
using asyncpg for high-performance async database operations.
"""

from .user_dao import UserDAO

__all__ = [
    "UserDAO",
]