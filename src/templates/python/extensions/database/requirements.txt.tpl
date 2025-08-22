# Database extension requirements
# Adds PostgreSQL database support to the core service

# PostgreSQL drivers
asyncpg==0.29.0
psycopg2-binary==2.9.9

# Database migrations (optional but recommended)
alembic==1.13.1

# Connection pooling and utilities
sqlalchemy[asyncio]==2.0.23