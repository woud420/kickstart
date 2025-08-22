# Core web framework
fastapi==0.104.1
uvicorn[standard]==0.24.0

# Database
asyncpg==0.29.0
psycopg2-binary==2.9.9

# Cache
redis==5.0.1

# Data validation and serialization  
pydantic==2.5.0
pydantic-settings==2.1.0

# Authentication and security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# HTTP client
httpx==0.25.2

# Environment and configuration
python-dotenv==1.0.0

# Monitoring and observability
structlog==23.2.0

# System monitoring
psutil==5.9.6

# Development and testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0

# Code quality
black==23.11.0
ruff==0.1.6
mypy==1.7.1

# Type stubs
types-redis==4.6.0.11
