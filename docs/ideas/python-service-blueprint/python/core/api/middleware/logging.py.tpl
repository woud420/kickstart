"""Logging middleware for API requests.

This module provides middleware for logging HTTP requests and responses,
including performance metrics, error tracking, and audit trails.
"""

import time
import uuid
import logging
from typing import Callable, Optional, Dict, Any
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import json

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """Middleware for logging HTTP requests and responses.
    
    Logs request details, response times, and error information
    for monitoring and debugging purposes.
    """
    
    def __init__(self, app):
        """Initialize the middleware.
        
        Args:
            app: FastAPI application instance
        """
        self.app = app
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details.
        
        Args:
            request: HTTP request
            call_next: Next middleware or route handler
            
        Returns:
            HTTP response
        """
        # Generate request ID for tracing
        request_id = str(uuid.uuid4())
        
        # Add request ID to headers for client reference
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Log request
        await self._log_request(request, request_id)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate response time
            process_time = time.time() - start_time
            
            # Add timing and request ID to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            # Log response
            await self._log_response(request, response, request_id, process_time)
            
            return response
            
        except Exception as e:
            # Calculate response time for errors
            process_time = time.time() - start_time
            
            # Log error
            await self._log_error(request, e, request_id, process_time)
            
            # Create error response
            error_response = JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": "Internal server error",
                    "request_id": request_id
                }
            )
            
            error_response.headers["X-Request-ID"] = request_id
            error_response.headers["X-Process-Time"] = str(process_time)
            
            return error_response

    async def _log_request(self, request: Request, request_id: str) -> None:
        """Log incoming request details.
        
        Args:
            request: HTTP request
            request_id: Unique request identifier
        """
        try:
            # Extract request info
            method = request.method
            url = str(request.url)
            headers = dict(request.headers)
            
            # Extract client info
            client_ip = self._get_client_ip(request)
            user_agent = headers.get("user-agent", "Unknown")
            
            # Extract body for POST/PUT requests (be careful with size)
            body = None
            if method in ["POST", "PUT", "PATCH"]:
                body = await self._get_request_body(request)
            
            # Create log entry
            log_data = {
                "event": "request",
                "request_id": request_id,
                "method": method,
                "url": url,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_ip": client_ip,
                "user_agent": user_agent,
                "headers": self._sanitize_headers(headers),
                "body": body
            }
            
            logger.info(
                f"Request {method} {request.url.path}",
                extra=log_data
            )
            
        except Exception as e:
            logger.error(f"Failed to log request: {e}")

    async def _log_response(
        self, 
        request: Request, 
        response: Response, 
        request_id: str, 
        process_time: float
    ) -> None:
        """Log response details.
        
        Args:
            request: HTTP request
            response: HTTP response
            request_id: Unique request identifier
            process_time: Request processing time in seconds
        """
        try:
            # Extract response info
            status_code = response.status_code
            headers = dict(response.headers)
            
            # Determine log level based on status code
            if status_code >= 500:
                log_level = logging.ERROR
            elif status_code >= 400:
                log_level = logging.WARNING
            else:
                log_level = logging.INFO
            
            # Create log entry
            log_data = {
                "event": "response",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "process_time_ms": round(process_time * 1000, 2),
                "response_headers": self._sanitize_headers(headers)
            }
            
            logger.log(
                log_level,
                f"Response {request.method} {request.url.path} {status_code} ({process_time*1000:.2f}ms)",
                extra=log_data
            )
            
            # Log slow requests
            if process_time > 1.0:  # More than 1 second
                logger.warning(
                    f"Slow request detected: {request.method} {request.url.path} took {process_time:.2f}s",
                    extra={**log_data, "event": "slow_request"}
                )
            
        except Exception as e:
            logger.error(f"Failed to log response: {e}")

    async def _log_error(
        self, 
        request: Request, 
        error: Exception, 
        request_id: str, 
        process_time: float
    ) -> None:
        """Log error details.
        
        Args:
            request: HTTP request
            error: Exception that occurred
            request_id: Unique request identifier
            process_time: Request processing time in seconds
        """
        try:
            # Create error log entry
            log_data = {
                "event": "error",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "process_time_ms": round(process_time * 1000, 2)
            }
            
            logger.error(
                f"Request error {request.method} {request.url.path}: {error}",
                extra=log_data,
                exc_info=True
            )
            
        except Exception as e:
            logger.error(f"Failed to log error: {e}")

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request.
        
        Args:
            request: HTTP request
            
        Returns:
            Client IP address
        """
        # Check for forwarded headers (behind proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP if there are multiple
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to direct connection
        if request.client:
            return request.client.host
        
        return "unknown"

    async def _get_request_body(self, request: Request) -> Optional[str]:
        """Extract request body safely.
        
        Args:
            request: HTTP request
            
        Returns:
            Request body as string, or None if too large/unavailable
        """
        try:
            # Check content type
            content_type = request.headers.get("content-type", "")
            
            # Only log JSON and form data
            if not any(ct in content_type.lower() for ct in ["json", "form", "text"]):
                return f"<{content_type}>"
            
            # Get body
            body = await request.body()
            
            # Limit body size to prevent huge logs
            max_size = 1024  # 1KB
            if len(body) > max_size:
                return f"<body too large: {len(body)} bytes>"
            
            # Try to decode as JSON for pretty printing
            if "json" in content_type.lower():
                try:
                    parsed = json.loads(body)
                    # Sanitize sensitive fields
                    return json.dumps(self._sanitize_json(parsed), indent=2)
                except json.JSONDecodeError:
                    pass
            
            # Return as string
            return body.decode("utf-8", errors="replace")
            
        except Exception as e:
            logger.debug(f"Failed to extract request body: {e}")
            return None

    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Remove sensitive information from headers.
        
        Args:
            headers: Request/response headers
            
        Returns:
            Sanitized headers
        """
        sensitive_headers = {
            "authorization", "cookie", "x-api-key", "x-auth-token",
            "authorization", "proxy-authorization"
        }
        
        sanitized = {}
        for key, value in headers.items():
            if key.lower() in sensitive_headers:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value
        
        return sanitized

    def _sanitize_json(self, data: Any) -> Any:
        """Remove sensitive information from JSON data.
        
        Args:
            data: JSON data to sanitize
            
        Returns:
            Sanitized JSON data
        """
        if isinstance(data, dict):
            sensitive_fields = {
                "password", "token", "secret", "key", "authorization",
                "credit_card", "ssn", "social_security"
            }
            
            sanitized = {}
            for key, value in data.items():
                if key.lower() in sensitive_fields:
                    sanitized[key] = "[REDACTED]"
                elif isinstance(value, (dict, list)):
                    sanitized[key] = self._sanitize_json(value)
                else:
                    sanitized[key] = value
            return sanitized
        
        elif isinstance(data, list):
            return [self._sanitize_json(item) for item in data]
        
        else:
            return data


def setup_request_logging(app):
    """Setup request logging middleware for the application.
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(RequestLoggingMiddleware)


def get_request_id(request: Request) -> Optional[str]:
    """Get request ID from current request.
    
    Args:
        request: HTTP request
        
    Returns:
        Request ID if available
    """
    return getattr(request.state, "request_id", None)


class AuditLogger:
    """Logger for audit trail events.
    
    Tracks important business events like user creation,
    data modifications, and security events.
    """
    
    def __init__(self):
        """Initialize audit logger."""
        self.logger = logging.getLogger("audit")
    
    def log_user_action(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> None:
        """Log a user action for audit trail.
        
        Args:
            user_id: ID of user performing action
            action: Action performed (create, update, delete, etc.)
            resource_type: Type of resource (user, profile, etc.)
            resource_id: ID of resource being acted upon
            details: Additional details about the action
            request_id: Request ID for correlation
        """
        audit_data = {
            "event": "user_action",
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
            "request_id": request_id,
            "timestamp": time.time()
        }
        
        self.logger.info(
            f"User {user_id} performed {action} on {resource_type}",
            extra=audit_data
        )
    
    def log_security_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> None:
        """Log a security event.
        
        Args:
            event_type: Type of security event (login_failed, token_invalid, etc.)
            user_id: ID of user involved (if applicable)
            ip_address: IP address of client
            details: Additional event details
            request_id: Request ID for correlation
        """
        audit_data = {
            "event": "security_event",
            "event_type": event_type,
            "user_id": user_id,
            "ip_address": ip_address,
            "details": details or {},
            "request_id": request_id,
            "timestamp": time.time()
        }
        
        self.logger.warning(
            f"Security event: {event_type}",
            extra=audit_data
        )


# Global audit logger instance
audit_logger = AuditLogger()