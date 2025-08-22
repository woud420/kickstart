"""Application settings and configuration.

This module handles environment-based configuration using Pydantic
settings with automatic validation and type conversion.
"""

from functools import lru_cache
from typing import Optional, List, Dict, Any
from pydantic import BaseSettings, Field, validator
import os
from pathlib import Path


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    db_host: str = Field(default="localhost", env="DB_HOST")
    db_port: int = Field(default=5432, env="DB_PORT")
    db_user: str = Field(default="postgres", env="DB_USER")
    db_password: str = Field(env="DB_PASSWORD")
    db_name: str = Field(env="DB_NAME")
    
    # Connection pool settings
    db_pool_min_size: int = Field(default=5, env="DB_POOL_MIN_SIZE")
    db_pool_max_size: int = Field(default=20, env="DB_POOL_MAX_SIZE")
    db_pool_max_queries: int = Field(default=50000, env="DB_POOL_MAX_QUERIES")
    db_pool_max_idle_time: float = Field(default=300.0, env="DB_POOL_MAX_IDLE_TIME")
    db_command_timeout: float = Field(default=60.0, env="DB_COMMAND_TIMEOUT")
    
    @validator('db_port')
    def validate_db_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Database port must be between 1 and 65535')
        return v
    
    @validator('db_pool_min_size')
    def validate_min_pool_size(cls, v):
        if v < 1:
            raise ValueError('Minimum pool size must be at least 1')
        return v
    
    @validator('db_pool_max_size')
    def validate_max_pool_size(cls, v, values):
        min_size = values.get('db_pool_min_size', 1)
        if v < min_size:
            raise ValueError('Maximum pool size must be greater than or equal to minimum pool size')
        return v


class RedisSettings(BaseSettings):
    """Redis cache configuration settings."""
    
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_ssl: bool = Field(default=False, env="REDIS_SSL")
    
    # Connection pool settings
    redis_pool_max_connections: int = Field(default=20, env="REDIS_POOL_MAX_CONNECTIONS")
    redis_socket_timeout: float = Field(default=5.0, env="REDIS_SOCKET_TIMEOUT")
    
    @validator('redis_port')
    def validate_redis_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Redis port must be between 1 and 65535')
        return v
    
    @validator('redis_db')
    def validate_redis_db(cls, v):
        if not 0 <= v <= 15:
            raise ValueError('Redis database number must be between 0 and 15')
        return v


class SecuritySettings(BaseSettings):
    """Security and authentication settings."""
    
    secret_key: str = Field(env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # Password hashing
    password_hash_rounds: int = Field(default=12, env="PASSWORD_HASH_ROUNDS")
    
    # CORS settings
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: List[str] = Field(default=["*"], env="CORS_ALLOW_METHODS")
    cors_allow_headers: List[str] = Field(default=["*"], env="CORS_ALLOW_HEADERS")
    
    @validator('secret_key')
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError('Secret key must be at least 32 characters long')
        return v
    
    @validator('access_token_expire_minutes')
    def validate_token_expire(cls, v):
        if v < 1:
            raise ValueError('Token expiration must be at least 1 minute')
        return v
    
    @validator('cors_origins', pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""
    
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    log_max_bytes: int = Field(default=10*1024*1024, env="LOG_MAX_BYTES")  # 10MB
    log_backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    # Structured logging
    log_json_format: bool = Field(default=False, env="LOG_JSON_FORMAT")
    
    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()


class ApplicationSettings(BaseSettings):
    """Main application settings."""
    
    # Application info
    app_name: str = Field(default="{{service_name}}", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    app_description: str = Field(default="{{service_name}} API", env="APP_DESCRIPTION")
    
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=1, env="WORKERS")
    
    # API settings
    api_prefix: str = Field(default="/api/v1", env="API_PREFIX")
    docs_url: Optional[str] = Field(default="/docs", env="DOCS_URL")
    redoc_url: Optional[str] = Field(default="/redoc", env="REDOC_URL")
    openapi_url: Optional[str] = Field(default="/openapi.json", env="OPENAPI_URL")
    
    # Rate limiting
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_period: int = Field(default=60, env="RATE_LIMIT_PERIOD")  # seconds
    
    # Feature flags
    feature_user_registration: bool = Field(default=True, env="FEATURE_USER_REGISTRATION")
    feature_email_notifications: bool = Field(default=True, env="FEATURE_EMAIL_NOTIFICATIONS")
    feature_file_uploads: bool = Field(default=False, env="FEATURE_FILE_UPLOADS")
    
    @validator('environment')
    def validate_environment(cls, v):
        valid_envs = ['development', 'staging', 'production', 'testing']
        if v.lower() not in valid_envs:
            raise ValueError(f'Environment must be one of: {valid_envs}')
        return v.lower()
    
    @validator('port')
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v
    
    @validator('workers')
    def validate_workers(cls, v):
        if v < 1:
            raise ValueError('Number of workers must be at least 1')
        return v
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.environment == "testing"


class ExternalServicesSettings(BaseSettings):
    """External services configuration."""
    
    # Email service (e.g., SendGrid, SES)
    email_enabled: bool = Field(default=False, env="EMAIL_ENABLED")
    email_backend: str = Field(default="console", env="EMAIL_BACKEND")  # console, smtp, sendgrid, ses
    
    # SMTP settings
    smtp_host: Optional[str] = Field(default=None, env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_user: Optional[str] = Field(default=None, env="SMTP_USER")
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=True, env="SMTP_USE_TLS")
    
    # SendGrid
    sendgrid_api_key: Optional[str] = Field(default=None, env="SENDGRID_API_KEY")
    
    # AWS SES
    aws_access_key_id: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field(default="us-east-1", env="AWS_REGION")
    
    # File storage
    file_storage_backend: str = Field(default="local", env="FILE_STORAGE_BACKEND")  # local, s3, gcs
    local_upload_dir: str = Field(default="uploads", env="LOCAL_UPLOAD_DIR")
    
    # AWS S3
    s3_bucket_name: Optional[str] = Field(default=None, env="S3_BUCKET_NAME")
    s3_region: str = Field(default="us-east-1", env="S3_REGION")
    
    # Monitoring and observability
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    datadog_api_key: Optional[str] = Field(default=None, env="DATADOG_API_KEY")


class Settings(
    ApplicationSettings,
    DatabaseSettings,
    RedisSettings,
    SecuritySettings,
    LoggingSettings,
    ExternalServicesSettings
):
    """Combined application settings."""
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        @classmethod
        def customise_sources(cls, init_settings, env_settings, file_secret_settings):
            # Priority: environment variables > .env file > defaults
            return (env_settings, file_secret_settings, init_settings)
    
    def __init__(self, **kwargs):
        """Initialize settings with validation."""
        super().__init__(**kwargs)
        self._validate_dependencies()
    
    def _validate_dependencies(self):
        """Validate interdependent settings."""
        # Email backend validation
        if self.email_enabled and self.email_backend == "smtp":
            if not self.smtp_host or not self.smtp_user:
                raise ValueError("SMTP host and user are required when email backend is 'smtp'")
        
        if self.email_enabled and self.email_backend == "sendgrid":
            if not self.sendgrid_api_key:
                raise ValueError("SendGrid API key is required when email backend is 'sendgrid'")
        
        # Production environment validation
        if self.is_production:
            if self.debug:
                raise ValueError("Debug mode should not be enabled in production")
            
            if self.docs_url or self.redoc_url or self.openapi_url:
                import warnings
                warnings.warn("API documentation endpoints are enabled in production")
    
    @property
    def database_url(self) -> str:
        """Get database connection URL."""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    @property
    def redis_url(self) -> str:
        """Get Redis connection URL."""
        auth = f":{self.redis_password}@" if self.redis_password else ""
        protocol = "rediss" if self.redis_ssl else "redis"
        return f"{protocol}://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    def get_cors_config(self) -> Dict[str, Any]:
        """Get CORS configuration for FastAPI."""
        return {
            "allow_origins": self.cors_origins,
            "allow_credentials": self.cors_allow_credentials,
            "allow_methods": self.cors_allow_methods,
            "allow_headers": self.cors_allow_headers,
        }
    
    def model_dump_safe(self) -> Dict[str, Any]:
        """Dump settings without sensitive information."""
        data = self.model_dump()
        
        # Remove sensitive fields
        sensitive_fields = [
            'db_password', 'redis_password', 'secret_key',
            'smtp_password', 'sendgrid_api_key', 'aws_secret_access_key',
            'sentry_dsn', 'datadog_api_key'
        ]
        
        for field in sensitive_fields:
            if field in data:
                data[field] = "[REDACTED]"
        
        return data


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings.
    
    Returns:
        Application settings instance
    """
    return Settings()


def load_settings_from_file(file_path: str) -> Settings:
    """Load settings from a specific file.
    
    Args:
        file_path: Path to the settings file
        
    Returns:
        Settings instance
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Settings file not found: {file_path}")
    
    return Settings(_env_file=file_path)


def validate_settings() -> None:
    """Validate all settings and raise errors if invalid."""
    try:
        settings = get_settings()
        print("✓ Settings validation passed")
        print(f"✓ Environment: {settings.environment}")
        print(f"✓ Application: {settings.app_name} v{settings.app_version}")
        print(f"✓ Database: {settings.db_host}:{settings.db_port}/{settings.db_name}")
        print(f"✓ Redis: {settings.redis_host}:{settings.redis_port}/{settings.redis_db}")
        
    except Exception as e:
        print(f"✗ Settings validation failed: {e}")
        raise


if __name__ == "__main__":
    # Allow running this file to validate settings
    validate_settings()