"""Main application entry point.

This is a minimal HTTP server using only Python standard library.
For enhanced functionality, use progressive enhancement flags:
- --database postgres (adds database support)
- --cache redis (adds caching support)  
- --auth jwt (adds authentication support)
"""

import json
import logging
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


class {{service_name|classname}}Handler(BaseHTTPRequestHandler):
    """HTTP request handler for {{service_name}} service."""
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == "/":
            self._send_json_response(200, {
                "name": "{{service_name}}",
                "version": "1.0.0",
                "description": "{{service_name}} microservice",
                "endpoints": {
                    "health": "/health",
                    "api": "/api/v1"
                }
            })
        elif path == "/health":
            self._handle_health_check()
        elif path.startswith("/api/v1"):
            self._handle_api_request(path)
        else:
            self._send_json_response(404, {
                "success": False,
                "message": "Endpoint not found",
                "error_code": "NOT_FOUND"
            })
    
    def do_POST(self):
        """Handle POST requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path.startswith("/api/v1"):
            self._handle_api_request(path)
        else:
            self._send_json_response(404, {
                "success": False,
                "message": "Endpoint not found",
                "error_code": "NOT_FOUND"
            })
    
    def _handle_health_check(self):
        """Handle health check endpoint."""
        health_data = {
            "healthy": True,
            "service": "{{service_name}}",
            "version": "1.0.0",
            "checks": {
                "application": {"healthy": True, "status": "running"}
            }
        }
        self._send_json_response(200, health_data)
    
    def _handle_api_request(self, path: str):
        """Handle API requests."""
        # Remove /api/v1 prefix
        api_path = path[7:] if path.startswith("/api/v1") else path
        
        if api_path == "/users" or api_path == "/users/":
            if self.command == "GET":
                self._handle_get_users()
            elif self.command == "POST":
                self._handle_create_user()
        elif api_path.startswith("/users/"):
            user_id = api_path.split("/")[-1]
            if self.command == "GET":
                self._handle_get_user(user_id)
        else:
            self._send_json_response(404, {
                "success": False,
                "message": "API endpoint not found",
                "error_code": "ENDPOINT_NOT_FOUND"
            })
    
    def _handle_get_users(self):
        """Handle GET /users request."""
        # Mock data - replace with actual implementation
        users = [
            {"id": "1", "username": "user1", "email": "user1@example.com"},
            {"id": "2", "username": "user2", "email": "user2@example.com"}
        ]
        self._send_json_response(200, {
            "success": True,
            "data": users,
            "count": len(users)
        })
    
    def _handle_get_user(self, user_id: str):
        """Handle GET /users/{id} request."""
        # Mock data - replace with actual implementation
        if user_id in ["1", "2"]:
            user = {
                "id": user_id,
                "username": f"user{user_id}",
                "email": f"user{user_id}@example.com",
                "full_name": f"User {user_id}",
                "created_at": "2024-01-01T00:00:00Z"
            }
            self._send_json_response(200, {
                "success": True,
                "data": user
            })
        else:
            self._send_json_response(404, {
                "success": False,
                "message": "User not found",
                "error_code": "USER_NOT_FOUND"
            })
    
    def _handle_create_user(self):
        """Handle POST /users request."""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Mock creation - replace with actual implementation
            user = {
                "id": "3",
                "username": data.get("username"),
                "email": data.get("email"),
                "full_name": data.get("full_name", ""),
                "created_at": "2024-01-01T00:00:00Z"
            }
            
            self._send_json_response(201, {
                "success": True,
                "message": "User created successfully",
                "data": user
            })
        except json.JSONDecodeError:
            self._send_json_response(400, {
                "success": False,
                "message": "Invalid JSON data",
                "error_code": "INVALID_JSON"
            })
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            self._send_json_response(500, {
                "success": False,
                "message": "Internal server error",
                "error_code": "INTERNAL_ERROR"
            })
    
    def _send_json_response(self, status_code: int, data: Dict[str, Any]):
        """Send JSON response."""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        
        response_json = json.dumps(data, indent=2)
        self.wfile.write(response_json.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override to use our logger."""
        logger.info(f"{self.address_string()} - {format % args}")


def run_server():
    """Run the HTTP server."""
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    
    server_address = (host, port)
    httpd = HTTPServer(server_address, {{service_name|classname}}Handler)
    
    logger.info(f"Starting {{service_name}} server on {host}:{port}")
    logger.info("Available endpoints:")
    logger.info("  GET  /            - Service information")
    logger.info("  GET  /health      - Health check")
    logger.info("  GET  /api/v1/users - List users")
    logger.info("  POST /api/v1/users - Create user")
    logger.info("  GET  /api/v1/users/{id} - Get user by ID")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        httpd.server_close()


async def health_check() -> Dict[str, Any]:
    """Perform application health check."""
    return {
        "healthy": True,
        "service": "{{service_name}}",
        "version": "1.0.0",
        "checks": {
            "application": {"healthy": True, "status": "running"}
        }
    }


if __name__ == "__main__":
    """Main entry point when running the module directly."""
    import argparse
    
    parser = argparse.ArgumentParser(description="{{service_name}} API Server")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    
    args = parser.parse_args()
    
    # Set environment variables
    os.environ["HOST"] = args.host
    os.environ["PORT"] = str(args.port)
    
    # Run the server
    run_server()