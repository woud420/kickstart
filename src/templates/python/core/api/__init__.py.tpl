"""API layer for HTTP request handling.

This module contains the API layer components including routes, middleware,
and dependencies for handling HTTP requests and responses using FastAPI.

The API layer is responsible for:
- HTTP request/response handling
- Input validation and serialization
- Authentication and authorization
- Request routing and middleware
- Dependency injection setup
"""

from .routes import user_router, health_router
from .middleware import *
from .dependencies import *

__all__ = [
    # Routes
    "user_router",
    "health_router",
    
    # Middleware
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "get_current_user_from_token",
    "get_optional_current_user",
    "require_active_user",
    "require_user_roles",
    "require_admin",
    "require_moderator",
    "RequestLoggingMiddleware",
    "setup_request_logging",
    "get_request_id",
    "audit_logger",
    
    # Dependencies
    "get_user_service",
    "get_user_repository",
    "get_user_dao",
    "get_current_user",
    "get_database_transaction",
    "get_pagination_params",
    "get_request_context",
    
    # Type annotations
    "UserServiceDep",
    "UserRepositoryDep",
    "UserDAODep",
    "CurrentUser",
    "DatabaseTransactionDep",
    "PaginationDep",
    "RequestContextDep",
]