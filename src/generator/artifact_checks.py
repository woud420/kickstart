"""Shared structural facts for read-only managed-artifact consumers."""

from pathlib import Path
import re


def owned_target(root: Path, relative: str) -> Path | None:
    path = root / relative
    try:
        return path if path.resolve(strict=path.is_symlink()).is_relative_to(root) else None
    except (OSError, RuntimeError):
        return None


def has_check_target(text: str) -> bool:
    """Recognize a literal target declaration without interpreting Make recipes."""
    return (
        re.search(r"^(?!\t)[ ]*(?:[^:\s#=$]+[ \t]+)*check(?:[ \t]+[^:\s#=$]+)*[ \t]*:(?!:*=)", text, re.MULTILINE)
        is not None
    )
