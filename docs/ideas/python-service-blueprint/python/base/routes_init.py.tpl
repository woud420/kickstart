"""API routes module.

This module contains all API route definitions organized by domain.
Routes handle HTTP requests, validate input, call services, and
return appropriate responses.
"""

{% block imports %}
from .user_routes import router as user_router
from .health import router as health_router
{% endblock %}

{% block exports %}
__all__ = [
    "user_router",
    "health_router",
]
{% endblock %}