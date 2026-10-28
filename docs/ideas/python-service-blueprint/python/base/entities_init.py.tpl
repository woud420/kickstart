"""Domain entities module.

This module contains all domain entities organized by business domain.
Entities represent the core business objects and contain business logic
and rules independent of storage or presentation concerns.
"""

{% block imports %}
from .user import *
{% endblock %}

{% block exports %}
__all__ = [
    # User domain entities
    "User",
    "UserProfile",
    "ProfileVisibility",
    "Gender",
    "SocialLinks",
    "Address",
]
{% endblock %}