"""Custom exception hierarchy for kickstart.

Every kickstart-specific error derives from `KickstartError`. Keeping the
models in their own module (separate from `error_handling.py`'s decorators
and context managers) lets call sites depend on the error types without
pulling in the handling machinery.
"""

from src.utils.types import ErrorContext, MutableErrorContext


class KickstartError(Exception):
    """Base exception for all kickstart-related errors."""

    def __init__(self, message: str, context: ErrorContext | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.context: MutableErrorContext = dict(context or {})

    def __str__(self) -> str:
        if not self.context:
            return self.message
        context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
        return f"{self.message} (context: {context_str})"


class ProjectCreationError(KickstartError):
    """Raised when project creation fails."""
    pass


class TemplateError(KickstartError):
    """Raised when template operations fail."""
    pass


class DirectoryCreationError(KickstartError):
    """Raised when directory creation fails."""
    pass


class FileOperationError(KickstartError):
    """Raised when file operations fail."""
    pass


class LanguageNotSupportedError(KickstartError):
    """Raised when an unsupported language is specified."""
    pass


class InvalidProjectNameError(KickstartError):
    """Raised when a project name fails validation."""
    pass


class UnsupportedProjectTypeError(KickstartError):
    """Raised when a project type has no creator."""
    pass


class MarkerError(KickstartError):
    """Raised when ownership fence markers are missing or malformed."""
    pass


class ManifestShapeError(KickstartError):
    """Raised when a scaffold manifest cannot be interpreted as a contract."""
    pass


class UnsupportedOptionError(KickstartError):
    """Raised when an option does not apply to the selected project type."""
    pass


class MissingCreateArgumentsError(KickstartError):
    """Raised when required create arguments are absent after prompting."""
    pass


class ExtensionError(KickstartError):
    """Raised when extension setup fails."""
    pass
