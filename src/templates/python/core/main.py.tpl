"""Main application entry point.

This module sets up the FastAPI application with proper dependency injection,
middleware configuration, and lifecycle management.
"""

import logging
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from config.settings import get_settings
from api.routes import user_router, health_router
from api.middleware import setup_request_logging
from infrastructure.database import initialize_database, shutdown_database
from infrastructure.cache import close_redis_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("app.log") if get_settings().log_file else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events.
    
    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting application...")
    
    try:
        # Initialize database
        await initialize_database()
        logger.info("Database initialized")
        
        # Other initialization tasks could go here
        # - Initialize cache connections
        # - Connect to external services
        # - Load ML models
        # - etc.
        
        logger.info("Application startup complete")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        sys.exit(1)
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    try:
        # Cleanup database connections
        await shutdown_database()
        logger.info("Database connections closed")
        
        # Cleanup cache connections
        await close_redis_client()
        logger.info("Cache connections closed")
        
        # Other cleanup tasks
        
        logger.info("Application shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during application shutdown: {e}")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    settings = get_settings()
    
    # Create FastAPI app with lifespan management
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        docs_url=settings.docs_url if not settings.is_production else None,
        redoc_url=settings.redoc_url if not settings.is_production else None,
        openapi_url=settings.openapi_url if not settings.is_production else None,
        lifespan=lifespan
    )
    
    # Add middleware
    setup_middleware(app)
    
    # Add routes
    setup_routes(app)
    
    # Add exception handlers
    setup_exception_handlers(app)
    
    return app


def setup_middleware(app: FastAPI) -> None:
    """Configure middleware for the application.
    
    Args:
        app: FastAPI application instance
    """
    settings = get_settings()
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        **settings.get_cors_config()
    )
    
    # Gzip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Request logging middleware
    setup_request_logging(app)
    
    logger.info("Middleware configured")


def setup_routes(app: FastAPI) -> None:
    """Configure routes for the application.
    
    Args:
        app: FastAPI application instance
    """
    settings = get_settings()
    
    # Include routers with API prefix
    app.include_router(health_router)  # Health checks don't need prefix
    app.include_router(user_router, prefix=settings.api_prefix)
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint returning basic API information."""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "description": settings.app_description,
            "docs_url": f"{settings.api_prefix}/docs" if settings.docs_url else None,
            "health_url": "/health"
        }
    
    logger.info("Routes configured")


def setup_exception_handlers(app: FastAPI) -> None:
    """Configure exception handlers for the application.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(500)
    async def internal_server_error(request, exc):
        """Handle internal server errors."""
        logger.error(f"Internal server error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Internal server error",
                "error_code": "INTERNAL_ERROR"
            }
        )
    
    @app.exception_handler(404)
    async def not_found_error(request, exc):
        """Handle not found errors."""
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "message": "Endpoint not found",
                "error_code": "NOT_FOUND"
            }
        )
    
    @app.exception_handler(422)
    async def validation_error(request, exc):
        """Handle validation errors."""
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "message": "Validation error",
                "error_code": "VALIDATION_ERROR",
                "details": exc.errors()
            }
        )
    
    logger.info("Exception handlers configured")


# Create the application instance
app = create_app()


def run_server():
    """Run the application server.
    
    This function is used when running the application directly
    or through a process manager like supervisord.
    """
    settings = get_settings()
    
    # Configure uvicorn
    uvicorn_config = {
        "app": "main:app",
        "host": settings.host,
        "port": settings.port,
        "reload": settings.debug and settings.is_development,
        "log_level": settings.log_level.lower(),
        "access_log": True,
        "workers": 1 if settings.debug else settings.workers,
    }
    
    logger.info(f"Starting server on {settings.host}:{settings.port}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Workers: {uvicorn_config['workers']}")
    
    # Run the server
    uvicorn.run(**uvicorn_config)


def run_development_server():
    """Run the development server with auto-reload.
    
    This is a convenience function for development that ensures
    the proper development configuration is used.
    """
    settings = get_settings()
    
    if not settings.is_development:
        logger.warning("Running development server in non-development environment")
    
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="debug",
        access_log=True,
        workers=1
    )


def run_production_server():
    """Run the production server with optimized settings.
    
    This function configures the server for production use with
    proper worker processes and performance optimizations.
    """
    settings = get_settings()
    
    if not settings.is_production:
        logger.warning("Running production server in non-production environment")
    
    # Production server configuration
    uvicorn_config = {
        "app": "main:app",
        "host": "0.0.0.0",
        "port": settings.port,
        "workers": settings.workers,
        "log_level": "info",
        "access_log": True,
        "proxy_headers": True,
        "forwarded_allow_ips": "*",
    }
    
    logger.info("Starting production server")
    logger.info(f"Configuration: {uvicorn_config}")
    
    uvicorn.run(**uvicorn_config)


async def health_check() -> Dict[str, Any]:
    """Perform application health check.
    
    This function can be called directly for health check purposes
    without starting the full web server.
    
    Returns:
        Health check results
    """
    from infrastructure.database import get_database_health
    from infrastructure.cache import get_cache_health
    
    try:
        # Check database
        db_health = await get_database_health()
        
        # Check cache (optional)
        cache_health = await get_cache_health()
        
        # Overall health status
        healthy = db_health.get("healthy", False)
        # Cache is optional, so don't fail if it's down
        
        return {
            "healthy": healthy,
            "checks": {
                "database": db_health,
                "cache": cache_health
            },
            "application": {
                "name": get_settings().app_name,
                "version": get_settings().app_version,
                "environment": get_settings().environment
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "healthy": False,
            "error": str(e)
        }


if __name__ == "__main__":
    """Main entry point when running the module directly."""
    import argparse
    import asyncio
    
    parser = argparse.ArgumentParser(description="{{service_name}} API Server")
    parser.add_argument(
        "--mode",
        choices=["dev", "prod", "health"],
        default="dev",
        help="Run mode (default: dev)"
    )
    parser.add_argument(
        "--host",
        default=None,
        help="Host to bind to"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to bind to"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of worker processes"
    )
    
    args = parser.parse_args()
    
    # Override settings if specified
    if args.host or args.port or args.workers:
        import os
        if args.host:
            os.environ["HOST"] = args.host
        if args.port:
            os.environ["PORT"] = str(args.port)
        if args.workers:
            os.environ["WORKERS"] = str(args.workers)
    
    # Run based on mode
    if args.mode == "dev":
        run_development_server()
    elif args.mode == "prod":
        run_production_server()
    elif args.mode == "health":
        async def check_health():
            result = await health_check()
            print(f"Health check result: {result}")
            return result["healthy"]
        
        healthy = asyncio.run(check_health())
        sys.exit(0 if healthy else 1)
    else:
        # Default to development server
        run_development_server()