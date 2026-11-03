"""API middleware components.

This module contains middleware components for request processing,
authentication, logging, and other cross-cutting concerns.
"""

{% block imports %}
from .auth import (
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user_from_token,
    get_optional_current_user,
    require_active_user,
    require_user_roles,
    require_admin,
    require_moderator,
    create_rate_limiter,
    rate_limit_strict,
    rate_limit_normal,
    rate_limit_generous,
    AuthenticationError,
    AuthorizationError
)
from .logging import (
    RequestLoggingMiddleware,
    setup_request_logging,
    get_request_id,
    AuditLogger,
    audit_logger
)
{% endblock %}

{% block exports %}
__all__ = [
    # Authentication
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "get_current_user_from_token",
    "get_optional_current_user",
    "require_active_user",
    "require_user_roles",
    "require_admin",
    "require_moderator",
    "create_rate_limiter",
    "rate_limit_strict",
    "rate_limit_normal",
    "rate_limit_generous",
    "AuthenticationError",
    "AuthorizationError",

    # Logging
    "RequestLoggingMiddleware",
    "setup_request_logging",
    "get_request_id",
    "AuditLogger",
    "audit_logger",
]
{% endblock %}