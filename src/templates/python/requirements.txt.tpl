# Core web framework
fastapi>=0.124,<1
uvicorn[standard]>=0.38,<1

# Database
asyncpg>=0.31,<1
psycopg[binary]>=3.2,<4

# Cache
redis[hiredis]>=7,<8

# Data validation and serialization  
pydantic>=2.12,<3
pydantic-settings>=2.12,<3
email-validator>=2.3,<3

# Authentication and security
python-jose[cryptography]>=3.5,<4
passlib[bcrypt]>=1.7,<2
python-multipart>=0.0.20,<1

# HTTP client
httpx>=0.28,<1

# Environment and configuration
python-dotenv>=1.2,<2

# Monitoring and observability
structlog>=25.5,<26

# System monitoring
psutil>=7,<8

# Development and testing
pytest>=8.4,<9
pytest-asyncio>=1.3,<2
pytest-cov>=7,<8

# Code quality
black>=25.11,<26
ruff>=0.14,<1
mypy>=1.20,<2
