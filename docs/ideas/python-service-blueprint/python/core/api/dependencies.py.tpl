"""FastAPI dependency injection setup.

This module configures dependency injection for the API layer,
providing services and other components to route handlers.
"""

from functools import lru_cache
from typing import Annotated
from fastapi import Depends
import asyncpg
import logging

from core.services.user_service import UserService
from repository.user_repo import UserRepository
from dao.postgres.user_dao import UserDAO
from infrastructure.database.connection import get_database_pool
from infrastructure.cache.redis_cache import get_redis_client
from config.settings import get_settings
from api.middleware.auth import get_current_user_from_token
from models.dto.responses import UserResponse

logger = logging.getLogger(__name__)

# Settings dependency
Settings = Annotated[object, Depends(get_settings)]

# Database dependencies
DatabasePool = Annotated[asyncpg.Pool, Depends(get_database_pool)]


@lru_cache()
def get_user_dao(pool: DatabasePool) -> UserDAO:
    """Get UserDAO instance with database pool.
    
    Args:
        pool: Database connection pool
        
    Returns:
        UserDAO instance
    """
    return UserDAO(pool)


@lru_cache()
def get_user_repository(pool: DatabasePool) -> UserRepository:
    """Get UserRepository instance with DAO dependency.
    
    Args:
        pool: Database connection pool
        
    Returns:
        UserRepository instance
    """
    dao = get_user_dao(pool)
    return UserRepository(dao)


@lru_cache()
def get_user_service(pool: DatabasePool) -> UserService:
    """Get UserService instance with all dependencies.
    
    Args:
        pool: Database connection pool
        
    Returns:
        UserService instance
    """
    repository = get_user_repository(pool)
    
    # Optional services can be None if not configured
    email_service = None  # Would be injected if configured
    notification_service = None  # Would be injected if configured
    
    return UserService(
        user_repository=repository,
        email_service=email_service,
        notification_service=notification_service
    )


# Dependency type annotations for easier use
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]
UserDAODep = Annotated[UserDAO, Depends(get_user_dao)]


# Authentication dependencies
async def get_current_user(
    user_service: UserServiceDep,
    token_data: dict = Depends(lambda: None)  # This would be properly implemented
) -> UserResponse:
    """Get current authenticated user.
    
    This is a wrapper around the auth middleware dependency
    that provides the user service injection.
    
    Args:
        user_service: User service for user lookup
        token_data: Token data from auth middleware
        
    Returns:
        Current user response
    """
    # This would integrate with the actual auth middleware
    # For now, returning a placeholder
    from api.middleware.auth import get_current_user_from_token
    return await get_current_user_from_token()


CurrentUser = Annotated[UserResponse, Depends(get_current_user)]


# Database transaction dependency
class DatabaseTransaction:
    """Database transaction context manager for dependency injection."""
    
    def __init__(self, pool: DatabasePool):
        """Initialize with database pool.
        
        Args:
            pool: Database connection pool
        """
        self.pool = pool
        self._connection = None
        self._transaction = None
    
    async def __aenter__(self):
        """Start database transaction.
        
        Returns:
            Database connection with active transaction
        """
        self._connection = await self.pool.acquire()
        self._transaction = self._connection.transaction()
        await self._transaction.start()
        return self._connection
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Complete database transaction.
        
        Args:
            exc_type: Exception type (if any)
            exc_val: Exception value (if any)  
            exc_tb: Exception traceback (if any)
        """
        try:
            if exc_type is None:
                await self._transaction.commit()
                logger.debug("Database transaction committed")
            else:
                await self._transaction.rollback()
                logger.warning(f"Database transaction rolled back due to {exc_type.__name__}")
        finally:
            await self.pool.release(self._connection)


async def get_database_transaction(pool: DatabasePool) -> DatabaseTransaction:
    """Get database transaction context manager.
    
    Args:
        pool: Database connection pool
        
    Returns:
        Database transaction context manager
    """
    return DatabaseTransaction(pool)


DatabaseTransactionDep = Annotated[DatabaseTransaction, Depends(get_database_transaction)]


# Cache dependencies
async def get_cache():
    """Get cache client (Redis).
    
    Returns:
        Cache client if available, None otherwise
    """
    try:
        return await get_redis_client()
    except Exception as e:
        logger.warning(f"Cache not available: {e}")
        return None


CacheDep = Annotated[object, Depends(get_cache)]


# Pagination helper
class PaginationParams:
    """Pagination parameters for list endpoints."""
    
    def __init__(self, page: int = 1, page_size: int = 20):
        """Initialize pagination parameters.
        
        Args:
            page: Page number (1-based)
            page_size: Items per page
        """
        self.page = max(1, page)
        self.page_size = min(100, max(1, page_size))
        self.offset = (self.page - 1) * self.page_size


def get_pagination_params(page: int = 1, page_size: int = 20) -> PaginationParams:
    """Get pagination parameters.
    
    Args:
        page: Page number
        page_size: Items per page
        
    Returns:
        Pagination parameters
    """
    return PaginationParams(page, page_size)


PaginationDep = Annotated[PaginationParams, Depends(get_pagination_params)]


# Request context
class RequestContext:
    """Request context information."""
    
    def __init__(self):
        """Initialize request context."""
        self.request_id = None
        self.user_id = None
        self.ip_address = None
        self.user_agent = None


def get_request_context(
    current_user: CurrentUser = None,
    request_id: str = Depends(lambda: None)  # Would be injected from middleware
) -> RequestContext:
    """Get request context information.
    
    Args:
        current_user: Current authenticated user (if any)
        request_id: Request ID from middleware
        
    Returns:
        Request context information
    """
    context = RequestContext()
    context.request_id = request_id
    
    if current_user:
        context.user_id = current_user.id
    
    return context


RequestContextDep = Annotated[RequestContext, Depends(get_request_context)]


# Health check dependencies
async def get_health_check_services() -> dict:
    """Get services for health check.
    
    Returns:
        Dictionary of service instances for health checking
    """
    services = {}
    
    try:
        # Database
        pool = await get_database_pool()
        services["database"] = pool
    except Exception as e:
        logger.error(f"Failed to get database pool for health check: {e}")
        services["database"] = None
    
    try:
        # Cache
        cache = await get_cache()
        services["cache"] = cache
    except Exception as e:
        logger.warning(f"Failed to get cache for health check: {e}")
        services["cache"] = None
    
    return services


HealthCheckServicesDep = Annotated[dict, Depends(get_health_check_services)]


# Service factory for dynamic service creation
class ServiceFactory:
    """Factory for creating service instances with proper dependency injection."""
    
    def __init__(self, pool: DatabasePool, cache: CacheDep = None):
        """Initialize service factory.
        
        Args:
            pool: Database connection pool
            cache: Cache client (optional)
        """
        self.pool = pool
        self.cache = cache
        self._services = {}
    
    def get_user_service(self) -> UserService:
        """Get or create UserService instance.
        
        Returns:
            UserService instance
        """
        if "user_service" not in self._services:
            dao = UserDAO(self.pool)
            repository = UserRepository(dao)
            self._services["user_service"] = UserService(
                user_repository=repository,
                email_service=None,  # Would be configured
                notification_service=None  # Would be configured
            )
        
        return self._services["user_service"]


def get_service_factory(
    pool: DatabasePool,
    cache: CacheDep = None
) -> ServiceFactory:
    """Get service factory instance.
    
    Args:
        pool: Database connection pool
        cache: Cache client (optional)
        
    Returns:
        Service factory instance
    """
    return ServiceFactory(pool, cache)


ServiceFactoryDep = Annotated[ServiceFactory, Depends(get_service_factory)]