# Core Python service requirements - no external dependencies
# This creates a minimal HTTP server using only standard library

# Standard library only - no external dependencies
# Use the default FastAPI scaffold for currently implemented service extensions.

# Development and testing (minimal set)
pytest>=8.4,<9
pytest-asyncio>=1.3,<2

# Code quality (optional but recommended)
black>=25.11,<26
ruff>=0.14,<1
mypy>=1.20,<2
