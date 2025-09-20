# Core Python service requirements - no external dependencies
# This creates a minimal HTTP server using only standard library

# Standard library only - no external dependencies
# For enhanced functionality, use extensions like:
# --database postgres (adds asyncpg, psycopg2)
# --cache redis (adds redis)
# --auth jwt (adds python-jose, passlib)

# Development and testing (minimal set)
pytest==7.4.3
pytest-asyncio==0.21.1

# Code quality (optional but recommended)
black==23.11.0
ruff==0.1.6
mypy==1.7.1