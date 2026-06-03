"""FastAPI application entrypoint for {{ service_name }}."""

import os

from fastapi import FastAPI

from .config import get_settings
from .routes import health_router, users_router


def create_app() -> FastAPI:
    """Create the FastAPI application."""
    settings = get_settings()
    app = FastAPI(title=settings.service_name, version="0.1.0")
    app.include_router(health_router)
    app.include_router(users_router)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "8080")),
    )
