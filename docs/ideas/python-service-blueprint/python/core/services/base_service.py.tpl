"""Base service class for business logic operations.

This module provides the abstract base service class that defines common
patterns for business logic services. Services coordinate between repositories,
handle business rules, and manage transactions.
"""

from abc import ABC
from typing import Any, Dict, List, Optional, TypeVar
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)


class BaseService(ABC):
    """Abstract base service for business logic operations.
    
    Services provide:
    - Business logic coordination
    - Transaction management 
    - Validation orchestration
    - Cross-repository operations
    - Business rule enforcement
    
    Services should be stateless and receive all dependencies via constructor
    injection to enable testing and maintain clear separation of concerns.
    """

    def __init__(self) -> None:
        """Initialize base service.
        
        Subclasses should override this to accept their specific dependencies
        (repositories, external clients, etc.) via constructor injection.
        """
        pass

    @asynccontextmanager
    async def transaction(self):
        """Business transaction context manager.
        
        Provides a transaction scope for operations that span multiple
        repositories or require atomicity guarantees.
        
        Usage:
            async with service.transaction() as tx:
                await service.create_user(user_data, tx)
                await service.send_welcome_email(user_data, tx)
                # All operations committed together
        
        Yields:
            Transaction context object
        """
        # Base implementation - subclasses should override to use their
        # specific database transaction mechanism
        try:
            yield None
            logger.debug("Transaction committed successfully")
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            raise

    def _validate_required_fields(self, data: Dict[str, Any], required_fields: List[str]) -> None:
        """Validate that required fields are present and not empty.
        
        Args:
            data: Data dictionary to validate
            required_fields: List of required field names
            
        Raises:
            ValidationError: If any required field is missing or empty
        """
        from .exceptions import ValidationError
        
        missing_fields = []
        empty_fields = []
        
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
            elif not data[field] or (isinstance(data[field], str) and not data[field].strip()):
                empty_fields.append(field)
        
        error_messages = []
        if missing_fields:
            error_messages.append(f"Missing required fields: {', '.join(missing_fields)}")
        if empty_fields:
            error_messages.append(f"Empty required fields: {', '.join(empty_fields)}")
            
        if error_messages:
            raise ValidationError("; ".join(error_messages))

    def _validate_field_length(
        self,
        value: str,
        field_name: str,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None
    ) -> None:
        """Validate field length constraints.
        
        Args:
            value: Field value to validate
            field_name: Name of the field (for error messages)
            min_length: Minimum required length
            max_length: Maximum allowed length
            
        Raises:
            ValidationError: If length constraints are violated
        """
        from .exceptions import ValidationError
        
        if not isinstance(value, str):
            return
            
        length = len(value.strip())
        
        if min_length is not None and length < min_length:
            raise ValidationError(f"{field_name} must be at least {min_length} characters long")
            
        if max_length is not None and length > max_length:
            raise ValidationError(f"{field_name} must be at most {max_length} characters long")

    def _validate_email_format(self, email: str) -> None:
        """Validate email format.
        
        Args:
            email: Email address to validate
            
        Raises:
            ValidationError: If email format is invalid
        """
        import re
        from .exceptions import ValidationError
        
        if not email:
            raise ValidationError("Email address is required")
            
        # Basic email regex pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(pattern, email):
            raise ValidationError("Invalid email address format")

    def _paginate_results(
        self,
        results: List[Any],
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Paginate results and return pagination metadata.
        
        Args:
            results: List of results to paginate
            page: Page number (1-based)
            page_size: Number of items per page
            
        Returns:
            Dictionary with paginated results and metadata
        """
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 20
            
        total_count = len(results)
        total_pages = (total_count + page_size - 1) // page_size
        
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        
        paginated_results = results[start_index:end_index]
        
        return {
            "data": paginated_results,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }

    def _log_operation(self, operation: str, entity_id: Optional[str] = None, **context) -> None:
        """Log business operation for audit trail.
        
        Args:
            operation: Operation name (e.g., "create_user", "update_profile")
            entity_id: ID of entity being operated on
            **context: Additional context for logging
        """
        log_data = {
            "operation": operation,
            "entity_id": entity_id,
            **context
        }
        
        logger.info(f"Business operation: {operation}", extra=log_data)

    def _handle_service_error(self, error: Exception, operation: str, entity_id: Optional[str] = None) -> None:
        """Handle and log service errors consistently.
        
        Args:
            error: Exception that occurred
            operation: Operation that failed
            entity_id: ID of entity being operated on
            
        Raises:
            ServiceError: Wrapped service error
        """
        from .exceptions import ServiceError
        
        logger.error(
            f"Service operation failed: {operation}",
            extra={
                "operation": operation,
                "entity_id": entity_id,
                "error_type": type(error).__name__,
                "error_message": str(error)
            },
            exc_info=True
        )
        
        # Re-raise service errors as-is
        if isinstance(error, ServiceError):
            raise
            
        # Wrap other errors in ServiceError
        raise ServiceError(f"Operation {operation} failed: {str(error)}") from error