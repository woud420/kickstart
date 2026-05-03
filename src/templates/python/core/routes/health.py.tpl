"""Health route."""

from fastapi import APIRouter
from pydantic import BaseModel

from ..config import get_settings


class HealthResponse(BaseModel):
    """Health response body."""

    status: str
    service: str
    environment: str


router = APIRouter(tags=["health"])


@router.get("/healthz", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return basic service health."""
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        environment=settings.environment,
    )
