"""Repository interfaces and simple in-memory implementation."""

from typing import Protocol
from uuid import uuid4

from .entities import User


class UserRepository(Protocol):
    """Repository contract for users."""

    def create(self, email: str) -> User:
        """Create a user."""
        ...

    def get(self, user_id: str) -> User | None:
        """Return a user by id."""
        ...


class InMemoryUserRepository:
    """In-memory user repository for generated examples and tests."""

    def __init__(self) -> None:
        self._users: dict[str, User] = {}

    def create(self, email: str) -> User:
        """Create a user."""
        user = User(id=str(uuid4()), email=email)
        self._users[user.id] = user
        return user

    def get(self, user_id: str) -> User | None:
        """Return a user by id."""
        return self._users.get(user_id)
