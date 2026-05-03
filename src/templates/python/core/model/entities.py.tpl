"""Domain entities."""

from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    """User domain entity."""

    id: str
    email: str
