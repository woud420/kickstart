# Application Settings
APP_NAME={{service_name}}
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
HOST=0.0.0.0
PORT=8000

# Database Settings (PostgreSQL)
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_NAME={{service_name}}_db

# Redis Settings (optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Security Settings
SECRET_KEY=your_secret_key_here_at_least_32_characters_long
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# External Services
EMAIL_ENABLED=false
EMAIL_BACKEND=console

# Feature Flags
FEATURE_USER_REGISTRATION=true
FEATURE_EMAIL_NOTIFICATIONS=false
