"""Typed file write plans for generators."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ContentFile:
    """Direct file content to write into a generated project."""

    target: str
    content: str
