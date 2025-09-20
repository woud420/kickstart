"""Database connection management.

This module handles database connection pooling, configuration,
and health checks for PostgreSQL using asyncpg.
"""

import asyncpg
import asyncio
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from functools import lru_cache

from config.settings import get_settings

logger = logging.getLogger(__name__)

# Global connection pool
_connection_pool: Optional[asyncpg.Pool] = None


async def create_database_pool() -> asyncpg.Pool:
    """Create and configure database connection pool.
    
    Returns:
        Configured asyncpg connection pool
        
    Raises:
        ConnectionError: If unable to connect to database
    """
    try:
        settings = get_settings()
        
        # Connection parameters
        connection_kwargs = {
            "host": settings.db_host,
            "port": settings.db_port,
            "user": settings.db_user,
            "password": settings.db_password,
            "database": settings.db_name,
            "min_size": settings.db_pool_min_size,
            "max_size": settings.db_pool_max_size,
            "max_queries": settings.db_pool_max_queries,
            "max_inactive_connection_lifetime": settings.db_pool_max_idle_time,
            "command_timeout": settings.db_command_timeout,
        }
        
        logger.info(f"Creating database pool: {settings.db_host}:{settings.db_port}/{settings.db_name}")
        
        pool = await asyncpg.create_pool(**connection_kwargs)
        
        # Test the connection
        async with pool.acquire() as connection:
            await connection.fetchval("SELECT 1")
            
        logger.info("Database connection pool created successfully")
        return pool
        
    except asyncpg.PostgresError as e:
        logger.error(f"PostgreSQL error creating connection pool: {e}")
        raise ConnectionError(f"Database connection failed: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error creating connection pool: {e}")
        raise ConnectionError(f"Database connection setup failed: {e}") from e


@lru_cache()
async def get_database_pool() -> asyncpg.Pool:
    """Get or create the global database connection pool.
    
    Returns:
        Database connection pool
    """
    global _connection_pool
    
    if _connection_pool is None:
        _connection_pool = await create_database_pool()
    
    return _connection_pool


async def close_database_pool() -> None:
    """Close the global database connection pool."""
    global _connection_pool
    
    if _connection_pool is not None:
        logger.info("Closing database connection pool")
        await _connection_pool.close()
        _connection_pool = None
        logger.info("Database connection pool closed")


@asynccontextmanager
async def get_database_connection():
    """Get a database connection from the pool.
    
    Usage:
        async with get_database_connection() as conn:
            result = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
    
    Yields:
        Database connection
    """
    pool = await get_database_pool()
    
    async with pool.acquire() as connection:
        try:
            yield connection
        except Exception as e:
            logger.error(f"Database operation failed: {e}")
            raise


@asynccontextmanager
async def get_database_transaction():
    """Get a database transaction.
    
    Usage:
        async with get_database_transaction() as tx:
            await tx.execute("INSERT INTO users ...")
            await tx.execute("INSERT INTO profiles ...")
            # Transaction committed automatically
    
    Yields:
        Database connection with active transaction
    """
    async with get_database_connection() as connection:
        async with connection.transaction():
            try:
                yield connection
                logger.debug("Database transaction committed")
            except Exception as e:
                logger.warning(f"Database transaction rolled back: {e}")
                raise


async def execute_query(query: str, *args) -> Any:
    """Execute a database query.
    
    Args:
        query: SQL query string
        *args: Query parameters
        
    Returns:
        Query result
    """
    async with get_database_connection() as connection:
        return await connection.fetchval(query, *args)


async def execute_many(query: str, args_list: list) -> None:
    """Execute a query multiple times with different parameters.
    
    Args:
        query: SQL query string
        args_list: List of parameter tuples
    """
    async with get_database_connection() as connection:
        await connection.executemany(query, args_list)


async def get_database_health() -> Dict[str, Any]:
    """Check database health and return status information.
    
    Returns:
        Database health information
    """
    try:
        start_time = asyncio.get_event_loop().time()
        
        async with get_database_connection() as connection:
            # Test basic connectivity
            result = await connection.fetchval("SELECT 1")
            
            # Get database version
            db_version = await connection.fetchval("SELECT version()")
            
            # Get connection pool stats
            pool = await get_database_pool()
            pool_stats = {
                "size": pool.get_size(),
                "min_size": pool.get_min_size(),
                "max_size": pool.get_max_size(),
                "idle_connections": pool.get_idle_size()
            }
            
            # Calculate response time
            response_time_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            
            return {
                "healthy": True,
                "response_time_ms": round(response_time_ms, 2),
                "database_version": db_version,
                "pool_stats": pool_stats,
                "test_query_result": result
            }
            
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "healthy": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


async def run_migrations() -> None:
    """Run database migrations.

    In a real application, this would integrate with migration tools
    or custom migration scripts.
    """
    try:
        logger.info("Starting database migrations")
        
        # This is a placeholder - implement actual migration logic
        async with get_database_connection() as connection:
            # Example: Create users table if it doesn't exist
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    full_name VARCHAR(100) NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    last_login_at TIMESTAMP WITH TIME ZONE,
                    deactivated_at TIMESTAMP WITH TIME ZONE,
                    profile_data JSONB DEFAULT '{}'::jsonb
                )
            """)
            
            # Create indexes
            await connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)
            """)
            
            await connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)
            """)
            
            await connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)
            """)
            
            # Example: Create user profiles table
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                    bio TEXT,
                    avatar_url VARCHAR(512),
                    date_of_birth DATE,
                    gender VARCHAR(20),
                    phone VARCHAR(20),
                    timezone VARCHAR(50) DEFAULT 'UTC',
                    language VARCHAR(10) DEFAULT 'en',
                    visibility VARCHAR(20) DEFAULT 'public',
                    social_links JSONB DEFAULT '{}'::jsonb,
                    address JSONB DEFAULT '{}'::jsonb,
                    interests TEXT[],
                    skills TEXT[],
                    occupation VARCHAR(100),
                    company VARCHAR(100),
                    education VARCHAR(200),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(user_id)
                )
            """)
            
        logger.info("Database migrations completed successfully")
        
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        raise


class DatabaseManager:
    """Database manager for lifecycle management."""
    
    def __init__(self):
        """Initialize database manager."""
        self.pool: Optional[asyncpg.Pool] = None
        self.is_initialized = False
    
    async def initialize(self) -> None:
        """Initialize database connections and run migrations."""
        try:
            logger.info("Initializing database manager")
            
            # Create connection pool
            self.pool = await create_database_pool()
            
            # Run migrations
            await run_migrations()
            
            self.is_initialized = True
            logger.info("Database manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database manager: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Shutdown database connections."""
        try:
            if self.pool:
                logger.info("Shutting down database manager")
                await self.pool.close()
                self.pool = None
                self.is_initialized = False
                logger.info("Database manager shutdown complete")
        except Exception as e:
            logger.error(f"Error during database shutdown: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check.
        
        Returns:
            Health check results
        """
        if not self.is_initialized:
            return {
                "healthy": False,
                "error": "Database manager not initialized"
            }
        
        return await get_database_health()


# Global database manager instance
db_manager = DatabaseManager()


async def initialize_database() -> None:
    """Initialize the database system."""
    await db_manager.initialize()


async def shutdown_database() -> None:
    """Shutdown the database system."""
    await db_manager.shutdown()
    await close_database_pool()


# Utility functions for common operations
async def fetch_one(query: str, *args) -> Optional[asyncpg.Record]:
    """Fetch one record from database.
    
    Args:
        query: SQL query
        *args: Query parameters
        
    Returns:
        Database record or None
    """
    async with get_database_connection() as connection:
        return await connection.fetchrow(query, *args)


async def fetch_many(query: str, *args) -> list[asyncpg.Record]:
    """Fetch multiple records from database.
    
    Args:
        query: SQL query
        *args: Query parameters
        
    Returns:
        List of database records
    """
    async with get_database_connection() as connection:
        return await connection.fetch(query, *args)


async def execute_command(query: str, *args) -> str:
    """Execute a database command.
    
    Args:
        query: SQL command
        *args: Command parameters
        
    Returns:
        Command execution result
    """
    async with get_database_connection() as connection:
        return await connection.execute(query, *args)