"""Health check API routes.

This module provides health check endpoints for monitoring application
status, dependencies, and system health.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
import logging
import os
import sys
import psutil
from typing import Dict, Any

from models.dto.responses import HealthCheckResponse
from models.schemas import HealthCheckResponseSchema
from infrastructure.database.connection import get_database_health
from infrastructure.cache.redis_cache import get_cache_health

logger = logging.getLogger(__name__)

# Application start time for uptime calculation
start_time = datetime.utcnow()

router = APIRouter(
    prefix="/health",
    tags=["health"],
    responses={
        200: {"model": HealthCheckResponseSchema, "description": "Service is healthy"},
        503: {"model": HealthCheckResponseSchema, "description": "Service is unhealthy"}
    }
)


@router.get(
    "/",
    response_model=HealthCheckResponseSchema,
    summary="Basic health check",
    description="Check if the application is running and responsive"
)
async def health_check() -> HealthCheckResponseSchema:
    """Basic health check endpoint.
    
    Returns basic application health status without checking dependencies.
    This endpoint should always be fast and reliable.
    
    Returns:
        Health check response with basic status
    """
    try:
        uptime_seconds = int((datetime.utcnow() - start_time).total_seconds())
        version = os.getenv("APP_VERSION", "1.0.0")
        
        health_response = HealthCheckResponse.healthy(version, uptime_seconds)
        
        return HealthCheckResponseSchema(**health_response.to_dict())
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        version = os.getenv("APP_VERSION", "1.0.0")
        health_response = HealthCheckResponse.unhealthy(version)
        
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_response.to_dict()
        )


@router.get(
    "/ready",
    response_model=Dict[str, Any],
    summary="Readiness check",
    description="Check if the application is ready to serve requests (includes dependency checks)"
)
async def readiness_check() -> Dict[str, Any]:
    """Readiness check with dependency verification.
    
    Checks all critical dependencies to determine if the application
    is ready to serve requests. This includes database, cache, and
    other external services.
    
    Returns:
        Detailed readiness status including dependency health
        
    Raises:
        HTTPException: If any critical dependency is unhealthy
    """
    try:
        logger.info("Performing readiness check")
        
        # Get basic health info
        uptime_seconds = int((datetime.utcnow() - start_time).total_seconds())
        version = os.getenv("APP_VERSION", "1.0.0")
        
        # Check dependencies
        checks = {}
        overall_healthy = True
        
        # Database health check
        try:
            db_health = await get_database_health()
            checks["database"] = db_health
            if not db_health.get("healthy", False):
                overall_healthy = False
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            checks["database"] = {"healthy": False, "error": str(e)}
            overall_healthy = False
        
        # Cache health check (optional - don't fail if cache is down)
        try:
            cache_health = await get_cache_health()
            checks["cache"] = cache_health
            # Cache is optional, so don't mark as unhealthy if it fails
        except Exception as e:
            logger.warning(f"Cache health check failed: {e}")
            checks["cache"] = {"healthy": False, "error": str(e), "optional": True}
        
        # System resource checks
        try:
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage('/')
            
            checks["system"] = {
                "healthy": True,
                "memory_percent": memory_info.percent,
                "disk_percent": disk_info.percent,
                "memory_available_gb": round(memory_info.available / (1024**3), 2),
                "disk_free_gb": round(disk_info.free / (1024**3), 2)
            }
            
            # Mark as unhealthy if resources are critically low
            if memory_info.percent > 90 or disk_info.percent > 95:
                checks["system"]["healthy"] = False
                overall_healthy = False
                
        except Exception as e:
            logger.warning(f"System health check failed: {e}")
            checks["system"] = {"healthy": False, "error": str(e)}
            # System checks are informational, don't fail readiness
        
        response_data = {
            "status": "ready" if overall_healthy else "not_ready",
            "timestamp": datetime.utcnow().isoformat(),
            "version": version,
            "uptime_seconds": uptime_seconds,
            "checks": checks
        }
        
        if not overall_healthy:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=response_data
            )
        
        logger.info("Readiness check passed")
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "error",
                "timestamp": datetime.utcnow().isoformat(),
                "version": os.getenv("APP_VERSION", "1.0.0"),
                "error": str(e)
            }
        )


@router.get(
    "/live",
    response_model=Dict[str, Any],
    summary="Liveness check",
    description="Check if the application is alive (basic process health)"
)
async def liveness_check() -> Dict[str, Any]:
    """Liveness check for container orchestration.
    
    Simple check to verify the application process is alive and responsive.
    This should be very lightweight and not check external dependencies.
    
    Returns:
        Liveness status information
    """
    try:
        uptime_seconds = int((datetime.utcnow() - start_time).total_seconds())
        version = os.getenv("APP_VERSION", "1.0.0")
        
        # Basic process health indicators
        process = psutil.Process(os.getpid())
        
        return {
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat(),
            "version": version,
            "uptime_seconds": uptime_seconds,
            "process": {
                "pid": os.getpid(),
                "memory_mb": round(process.memory_info().rss / (1024*1024), 2),
                "cpu_percent": process.cpu_percent(),
                "threads": process.num_threads()
            },
            "python": {
                "version": sys.version,
                "executable": sys.executable
            }
        }
        
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "dead",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )


@router.get(
    "/metrics",
    response_model=Dict[str, Any],
    summary="Application metrics",
    description="Get detailed application metrics for monitoring"
)
async def get_metrics() -> Dict[str, Any]:
    """Get application metrics for monitoring.
    
    Returns detailed metrics about application performance,
    resource usage, and operational statistics.
    
    Returns:
        Application metrics dictionary
    """
    try:
        uptime_seconds = int((datetime.utcnow() - start_time).total_seconds())
        version = os.getenv("APP_VERSION", "1.0.0")
        
        # Process metrics
        process = psutil.Process(os.getpid())
        process_info = process.as_dict(attrs=[
            'pid', 'memory_info', 'cpu_percent', 'cpu_times',
            'num_threads', 'open_files', 'connections'
        ])
        
        # System metrics
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Application-specific metrics would go here
        # For example: request counts, error rates, etc.
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "version": version,
            "uptime_seconds": uptime_seconds,
            "system": {
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_percent": memory.percent
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "used_percent": round((disk.used / disk.total) * 100, 2)
                },
                "cpu_count": psutil.cpu_count(),
                "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            },
            "process": {
                "pid": process_info['pid'],
                "memory": {
                    "rss_mb": round(process_info['memory_info'].rss / (1024*1024), 2),
                    "vms_mb": round(process_info['memory_info'].vms / (1024*1024), 2)
                },
                "cpu": {
                    "percent": process_info['cpu_percent'],
                    "user_time": process_info['cpu_times'].user,
                    "system_time": process_info['cpu_times'].system
                },
                "threads": process_info['num_threads'],
                "open_files": len(process_info.get('open_files', [])),
                "connections": len(process_info.get('connections', []))
            },
            "python": {
                "version": sys.version_info[:3],
                "implementation": sys.implementation.name,
                "executable": sys.executable
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to retrieve metrics", "details": str(e)}
        )