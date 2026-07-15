"""Centralized error handling utilities for kickstart generators.

This module provides standardized error handling decorators, context
managers, and utilities to eliminate duplication across the codebase. The
exception types themselves live in `src.utils.errors`.
"""

import logging
import functools
from collections.abc import Callable, Generator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import ParamSpec, TypeVar
from src.utils.errors import (
    DirectoryCreationError,
    FileOperationError,
    KickstartError,
    LanguageNotSupportedError,
)
from src.utils.logger import warn
from src.utils.types import ErrorContext, ErrorContextValue

logger = logging.getLogger(__name__)

# The handling API only. Exception classes live in `src.utils.errors` and
# are deliberately absent: importing an error class from this module
# half-worked (only the four classes imported above resolved), which is
# exactly how PR #81 merged green and broke master. Import error classes
# from `src.utils.errors`; `make check` enforces this via the import
# hygiene audit.
__all__ = [
    "error_context",
    "handle_file_operations",
    "handle_template_operations",
    "handle_directory_operations",
    "handle_http_operations",
    "safe_operation",
    "safe_operation_context",
    "ErrorCollector",
    "format_error_message",
    "log_operation_result",
    "batch_operation_wrapper",
    "validate_language_support",
    "ensure_directory_exists",
    "safe_binary_write",
    "safe_file_write",
    "safe_file_copy",
]

P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T")


# Error Context Manager
@contextmanager
def error_context(operation: str, **context: ErrorContextValue) -> Generator[None, None, None]:
    """Context manager for standardized error handling with operation context.

    Args:
        operation: Description of the operation being performed
        **context: Additional context information

    Yields:
        None

    Raises:
        KickstartError: Re-raises any exception as KickstartError with context
    """
    try:
        logger.debug(f"Starting operation: {operation}")
        yield
        logger.debug(f"Completed operation: {operation}")
    except KickstartError:
        # Re-raise KickstartError as-is
        raise
    except Exception as e:
        error_msg = f"Operation '{operation}' failed: {e}"
        logger.error(error_msg, extra=context, exc_info=True)
        raise KickstartError(error_msg, context) from e


# Error Handling Decorators
def handle_file_operations(
    default_return: R,
    log_errors: bool = True,
    reraise: bool = False
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator for standardizing file operation error handling.

    Args:
        default_return: Value to return on error (if not reraising)
        log_errors: Whether to log errors
        reraise: Whether to reraise exceptions as KickstartError

    Returns:
        Decorated function
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return func(*args, **kwargs)
            except (OSError, FileNotFoundError, PermissionError) as e:
                if log_errors:
                    logger.error(f"File operation failed in {func.__name__}: {e}", exc_info=True)
                if reraise:
                    raise FileOperationError(f"File operation failed: {e}") from e
                return default_return
        return wrapper
    return decorator


def handle_template_operations(
    default_return: R,
    log_errors: bool = True
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator for standardizing template operation error handling.

    Args:
        default_return: Value to return on error
        log_errors: Whether to log errors

    Returns:
        Decorated function
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.error(f"Template operation failed in {func.__name__}: {e}", exc_info=True)
                # Always use warn for user-facing feedback
                warn(f"Template operation failed: {e}")
                return default_return
        return wrapper
    return decorator


def handle_directory_operations(
    default_return: R,
    log_errors: bool = True
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator for standardizing directory operation error handling.

    Args:
        default_return: Value to return on error
        log_errors: Whether to log errors

    Returns:
        Decorated function
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return func(*args, **kwargs)
            except OSError as e:
                if log_errors:
                    logger.error(f"Directory operation failed in {func.__name__}: {e}", exc_info=True)
                warn(f"Directory operation failed: {e}")
                return default_return
        return wrapper
    return decorator


def handle_http_operations(
    operation_name: str,
    default_return: R,
    log_errors: bool = True,
    reraise: bool = False
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator for standardizing HTTP operation error handling.

    Handles common HTTP exceptions including requests.RequestException,
    connection errors, timeouts, and HTTP status errors.

    Args:
        operation_name: Name of the operation for logging
        default_return: Value to return on error
        log_errors: Whether to log errors
        reraise: Whether to reraise exceptions as KickstartError

    Returns:
        Decorated function
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Import here to avoid circular dependency issues
                import requests

                error_msg = f"{operation_name} failed: {e}"

                if isinstance(e, requests.RequestException):
                    if hasattr(e, 'response') and e.response is not None:
                        error_msg = f"{operation_name} failed with HTTP {e.response.status_code}: {e}"
                    else:
                        error_msg = f"{operation_name} failed with network error: {e}"

                if log_errors:
                    logger.error(f"HTTP operation failed in {func.__name__}: {error_msg}", exc_info=True)

                if reraise:
                    raise KickstartError(error_msg) from e

                return default_return
        return wrapper
    return decorator


def safe_operation(
    operation_name: str,
    reraise_as: type[Exception] | None = None,
    default_return: R | None = None,
    log_errors: bool = True
) -> Callable[[Callable[P, R | None]], Callable[P, R | None]]:
    """Generic decorator for safe operation execution with standardized error handling.

    Args:
        operation_name: Name of the operation for logging
        reraise_as: Exception type to reraise as (if any)
        default_return: Value to return on error
        log_errors: Whether to log errors

    Returns:
        Decorated function
    """
    def decorator(func: Callable[P, R | None]) -> Callable[P, R | None]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | None:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.error(f"{operation_name} failed in {func.__name__}: {e}", exc_info=True)

                if reraise_as:
                    raise reraise_as(f"{operation_name} failed: {e}") from e

                return default_return
        return wrapper
    return decorator


@contextmanager
def safe_operation_context(
    operation_name: str,
    log_errors: bool = True,
    suppress_exceptions: bool = True
) -> Generator[None, None, None]:
    """Context manager for safe operation execution.

    Args:
        operation_name: Name of the operation for logging
        log_errors: Whether to log errors
        suppress_exceptions: Whether to suppress exceptions

    Yields:
        None
    """
    try:
        logger.debug(f"Starting safe operation: {operation_name}")
        yield
        logger.debug(f"Completed safe operation: {operation_name}")
    except Exception as e:
        if log_errors:
            logger.error(f"Safe operation '{operation_name}' failed: {e}", exc_info=True)
        if not suppress_exceptions:
            raise


# Error Collection and Reporting
class ErrorCollector:
    """Collects and manages errors during batch operations."""

    def __init__(self, operation_name: str) -> None:
        self.operation_name = operation_name
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.success_count = 0
        self.total_count = 0

    def add_error(self, error: str) -> None:
        """Add an error to the collection."""
        self.errors.append(error)
        logger.error(f"[{self.operation_name}] Error: {error}")

    def add_warning(self, warning: str) -> None:
        """Add a warning to the collection."""
        self.warnings.append(warning)
        logger.warning(f"[{self.operation_name}] Warning: {warning}")

    def increment_success(self) -> None:
        """Increment success counter."""
        self.success_count += 1

    def increment_total(self) -> None:
        """Increment total counter."""
        self.total_count += 1

    def has_errors(self) -> bool:
        """Check if any errors were collected."""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """Check if any warnings were collected."""
        return len(self.warnings) > 0

    def get_summary(self) -> str:
        """Get a summary of the operation results."""
        summary_parts = [f"{self.success_count}/{self.total_count} operations successful"]

        if self.errors:
            summary_parts.append(f"{len(self.errors)} errors")

        if self.warnings:
            summary_parts.append(f"{len(self.warnings)} warnings")

        return f"[{self.operation_name}] " + ", ".join(summary_parts)

    def log_summary(self) -> None:
        """Log the operation summary."""
        summary = self.get_summary()

        if self.has_errors():
            logger.error(summary)
            warn(f"{self.operation_name} completed with errors")
        elif self.has_warnings():
            logger.warning(summary)
        else:
            logger.info(summary)

    def report_failures(self) -> None:
        """Report all collected failures to the user."""
        if self.errors:
            error_list = '; '.join(self.errors)
            warn(f"{self.operation_name} errors: {error_list}")

        if self.warnings:
            warning_list = '; '.join(self.warnings)
            logger.warning(f"{self.operation_name} warnings: {warning_list}")


# Utility Functions
def format_error_message(
    operation: str,
    target: str | Path,
    error: Exception,
    context: ErrorContext | None = None
) -> str:
    """Format a standardized error message.

    Args:
        operation: The operation that failed
        target: The target file/directory/resource
        error: The exception that occurred
        context: Additional context information

    Returns:
        Formatted error message
    """
    base_msg = f"{operation} failed for '{target}': {error}"

    if context:
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        base_msg += f" (context: {context_str})"

    return base_msg


def log_operation_result(
    operation: str,
    success: bool,
    target: str | Path | None = None,
    error: Exception | None = None,
    context: ErrorContext | None = None
) -> None:
    """Log the result of an operation with standardized formatting.

    Args:
        operation: The operation that was performed
        success: Whether the operation succeeded
        target: The target file/directory/resource (optional)
        error: The exception if operation failed (optional)
        context: Additional context information (optional)
    """
    target_str = f" for '{target}'" if target else ""

    if success:
        logger.debug(f"{operation} succeeded{target_str}")
    else:
        resolved_error = error or Exception("Unknown error")
        error_msg = format_error_message(operation, target or "unknown", resolved_error, context)
        logger.error(error_msg, exc_info=resolved_error)


def batch_operation_wrapper(
    items: Sequence[T],
    operation_func: Callable[[T], bool],
    operation_name: str,
    item_name_func: Callable[[T], str] | None = None
) -> ErrorCollector:
    """Execute a batch operation with standardized error collection.

    Args:
        items: List of items to process
        operation_func: Function to apply to each item (should return bool for success)
        operation_name: Name of the operation for logging
        item_name_func: Function to get string representation of item (optional)

    Returns:
        ErrorCollector with results
    """
    collector = ErrorCollector(operation_name)

    for item in items:
        collector.increment_total()
        item_name = item_name_func(item) if item_name_func else str(item)

        try:
            if operation_func(item):
                collector.increment_success()
                logger.debug(f"[{operation_name}] Success: {item_name}")
            else:
                collector.add_error(f"Operation failed for {item_name}")
        except Exception as e:
            collector.add_error(f"Exception processing {item_name}: {e}")

    collector.log_summary()
    return collector


# Common Error Patterns
def validate_language_support(language: str, supported_languages: Sequence[str]) -> None:
    """Validate that a language is supported.

    Args:
        language: The language to validate
        supported_languages: List of supported languages

    Raises:
        LanguageNotSupportedError: If language is not supported
    """
    if language not in supported_languages:
        raise LanguageNotSupportedError(
            f"Language '{language}' is not supported. Supported languages: {', '.join(supported_languages)}"
        )


def ensure_directory_exists(directory: Path, create: bool = True) -> bool:
    """Ensure a directory exists, optionally creating it.

    Args:
        directory: The directory path
        create: Whether to create the directory if it doesn't exist

    Returns:
        True if directory exists or was created successfully

    Raises:
        DirectoryCreationError: If directory creation fails
    """
    if directory.exists():
        return True

    if not create:
        return False

    try:
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created directory: {directory}")
        return True
    except OSError as e:
        raise DirectoryCreationError(f"Failed to create directory '{directory}': {e}") from e


def safe_binary_write(
    file_path: Path,
    content: bytes,
    create_dirs: bool = True,
    permissions: int | None = None
) -> bool:
    """Safely write binary content to a file with error handling.

    Args:
        file_path: Path to the file
        content: Binary content to write
        create_dirs: Whether to create parent directories
        permissions: Optional file permissions (e.g., 0o755)

    Returns:
        True if file was written successfully

    Raises:
        FileOperationError: If file writing fails
    """
    try:
        if create_dirs:
            ensure_directory_exists(file_path.parent)

        file_path.write_bytes(content)

        if permissions is not None:
            file_path.chmod(permissions)

        logger.debug(f"Successfully wrote binary file: {file_path}")
        return True
    except OSError as e:
        raise FileOperationError(f"Failed to write binary file '{file_path}': {e}") from e


def safe_file_write(
    file_path: Path,
    content: str,
    encoding: str = 'utf-8',
    create_dirs: bool = True
) -> bool:
    """Safely write content to a file with error handling.

    Args:
        file_path: Path to the file
        content: Content to write
        encoding: File encoding
        create_dirs: Whether to create parent directories

    Returns:
        True if file was written successfully

    Raises:
        FileOperationError: If file writing fails
    """
    try:
        if create_dirs:
            ensure_directory_exists(file_path.parent)

        file_path.write_text(content, encoding=encoding)
        logger.debug(f"Successfully wrote file: {file_path}")
        return True
    except OSError as e:
        raise FileOperationError(f"Failed to write file '{file_path}': {e}") from e


def safe_file_copy(
    source_path: Path,
    target_path: Path,
    create_dirs: bool = True,
    preserve_metadata: bool = True
) -> bool:
    """Safely copy a file with error handling.

    Args:
        source_path: Source file path
        target_path: Target file path
        create_dirs: Whether to create parent directories
        preserve_metadata: Whether to preserve file metadata

    Returns:
        True if file was copied successfully

    Raises:
        FileOperationError: If file copying fails
    """
    import shutil

    try:
        if create_dirs:
            ensure_directory_exists(target_path.parent)

        if preserve_metadata:
            shutil.copy2(source_path, target_path)
        else:
            shutil.copy(source_path, target_path)

        logger.debug(f"Successfully copied file: {source_path} -> {target_path}")
        return True
    except (OSError, shutil.Error) as e:
        raise FileOperationError(f"Failed to copy file '{source_path}' to '{target_path}': {e}") from e
