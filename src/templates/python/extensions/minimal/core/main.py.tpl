"""Main application entry point.

This is a minimal HTTP server using only the Python standard library.
Use the default FastAPI scaffold for currently implemented service extensions.
"""

import json
import logging
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

type JsonValue = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
type JsonObject = dict[str, JsonValue]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


class {{service_name|classname}}Handler(BaseHTTPRequestHandler):
    """HTTP request handler for {{service_name}} service."""

    def do_GET(self) -> None:
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path == "/":
            self._send_json_response(
                200,
                {
                    "name": "{{service_name}}",
                    "version": "1.0.0",
                    "description": "{{service_name}} microservice",
                    "endpoints": {"health": "/health"},
                },
            )
        elif path == "/health":
            self._handle_health_check()
        else:
            self._send_error_response(404, "Endpoint not found", "NOT_FOUND")

    def _handle_health_check(self) -> None:
        """Handle health check endpoint."""
        health_data: JsonObject = {
            "status": "ok",
            "healthy": True,
            "service": "{{service_name}}",
            "version": "1.0.0",
            "checks": {"application": {"healthy": True, "status": "running"}},
        }
        self._send_json_response(200, health_data)

    def _send_error_response(self, status_code: int, message: str, error_code: str) -> None:
        """Send a standard API error response."""
        self._send_json_response(
            status_code,
            {
                "success": False,
                "message": message,
                "error_code": error_code,
            },
        )

    def _send_json_response(self, status_code: int, data: JsonObject) -> None:
        """Send JSON response."""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

        response_json = json.dumps(data, indent=2)
        self.wfile.write(response_json.encode("utf-8"))

    def log_message(self, format: str, *args: str | int | float) -> None:
        """Route request logs through the application logger."""
        logger.info(f"{self.address_string()} - {format % args}")


def run_server() -> None:
    """Run the HTTP server."""
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8080"))

    server_address = (host, port)
    httpd = HTTPServer(server_address, {{service_name|classname}}Handler)

    logger.info(f"Starting {{service_name}} server on {host}:{port}")
    logger.info("Available endpoints:")
    logger.info("  GET  /            - Service information")
    logger.info("  GET  /health      - Health check")
    logger.info("  GET  /api/v1/users/{id} - Get user by ID")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        httpd.server_close()


async def health_check() -> JsonObject:
    """Perform application health check."""
    return {
        "status": "ok",
        "healthy": True,
        "service": "{{service_name}}",
        "version": "1.0.0",
        "checks": {"application": {"healthy": True, "status": "running"}},
    }


if __name__ == "__main__":
    """Main entry point when running the module directly."""
    import argparse

    default_host = os.environ.get("HOST", "0.0.0.0")
    default_port = int(os.environ.get("PORT", "8080"))

    parser = argparse.ArgumentParser(description="{{service_name}} API Server")
    parser.add_argument(
        "--host",
        default=default_host,
        help=f"Host to bind to (default: {default_host}, override with HOST env var)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=default_port,
        help=f"Port to bind to (default: {default_port}, override with PORT env var)",
    )

    args = parser.parse_args()

    # Set environment variables so run_server picks them up
    os.environ["HOST"] = args.host
    os.environ["PORT"] = str(args.port)

    # Run the server
    run_server()
