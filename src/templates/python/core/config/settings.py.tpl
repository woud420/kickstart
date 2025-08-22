"""Application settings and configuration.

This module provides configuration management using environment variables
with sensible defaults for core functionality.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class Settings:
    """Application settings loaded from environment variables."""
    
    # Application settings
    app_name: str = field(default="{{service_name}}")
    app_version: str = field(default="1.0.0")
    app_description: str = field(default="{{service_name}} microservice")
    environment: str = field(default="development")
    debug: bool = field(default=True)
    
    # Server settings
    host: str = field(default="127.0.0.1")
    port: int = field(default=8000)
    workers: int = field(default=1)
    
    # Logging settings
    log_level: str = field(default="INFO")
    log_file: Optional[str] = field(default=None)
    
    # API settings
    api_prefix: str = field(default="/api/v1")
    docs_url: Optional[str] = field(default="/docs")
    redoc_url: Optional[str] = field(default="/redoc")
    openapi_url: Optional[str] = field(default="/openapi.json")
    
    # CORS settings
    cors_origins: list[str] = field(default_factory=lambda: ["*"])
    cors_credentials: bool = field(default=True)
    cors_methods: list[str] = field(default_factory=lambda: ["*"])
    cors_headers: list[str] = field(default_factory=lambda: ["*"])
    
    # Security settings (minimal for core)
    secret_key: str = field(default="your-secret-key-change-in-production")
    
    # Feature flags
    feature_user_registration: bool = field(default=True)
    feature_user_profiles: bool = field(default=True)
    
    def __post_init__(self):
        """Load settings from environment variables."""
        self.app_name = os.environ.get("APP_NAME", self.app_name)
        self.app_version = os.environ.get("APP_VERSION", self.app_version)
        self.app_description = os.environ.get("APP_DESCRIPTION", self.app_description)
        self.environment = os.environ.get("ENVIRONMENT", self.environment)
        self.debug = os.environ.get("DEBUG", "true").lower() in ("true", "1", "yes", "on")
        
        # Server settings
        self.host = os.environ.get("HOST", self.host)
        self.port = int(os.environ.get("PORT", str(self.port)))
        self.workers = int(os.environ.get("WORKERS", str(self.workers)))
        
        # Logging settings
        self.log_level = os.environ.get("LOG_LEVEL", self.log_level)
        self.log_file = os.environ.get("LOG_FILE")
        
        # API settings
        self.api_prefix = os.environ.get("API_PREFIX", self.api_prefix)
        
        # Disable docs in production
        if self.is_production:
            self.docs_url = None
            self.redoc_url = None
            self.openapi_url = None
        
        # CORS settings
        cors_origins_env = os.environ.get("CORS_ORIGINS")
        if cors_origins_env:
            self.cors_origins = [origin.strip() for origin in cors_origins_env.split(",")]
        
        self.cors_credentials = os.environ.get("CORS_CREDENTIALS", "true").lower() in ("true", "1", "yes", "on")
        
        # Security settings
        self.secret_key = os.environ.get("SECRET_KEY", self.secret_key)
        
        # Feature flags
        self.feature_user_registration = os.environ.get("FEATURE_USER_REGISTRATION", "true").lower() in ("true", "1", "yes", "on")
        self.feature_user_profiles = os.environ.get("FEATURE_USER_PROFILES", "true").lower() in ("true", "1", "yes", "on")
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() in ("development", "dev", "local")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() in ("production", "prod")
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.environment.lower() in ("testing", "test")
    
    def get_cors_config(self) -> Dict[str, Any]:
        """Get CORS configuration for middleware."""
        return {
            "allow_origins": self.cors_origins,
            "allow_credentials": self.cors_credentials,
            "allow_methods": self.cors_methods,
            "allow_headers": self.cors_headers
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            "app_name": self.app_name,
            "app_version": self.app_version,
            "app_description": self.app_description,
            "environment": self.environment,
            "debug": self.debug,
            "host": self.host,
            "port": self.port,
            "workers": self.workers,
            "log_level": self.log_level,
            "log_file": self.log_file,
            "api_prefix": self.api_prefix,
            "docs_url": self.docs_url,
            "redoc_url": self.redoc_url,
            "openapi_url": self.openapi_url,
            "cors_origins": self.cors_origins,
            "cors_credentials": self.cors_credentials,
            "cors_methods": self.cors_methods,
            "cors_headers": self.cors_headers,
            "secret_key": "***" if self.secret_key else None,  # Hide secret
            "feature_user_registration": self.feature_user_registration,
            "feature_user_profiles": self.feature_user_profiles,
            "is_development": self.is_development,
            "is_production": self.is_production,
            "is_testing": self.is_testing
        }


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings singleton.
    
    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment variables.
    
    Returns:
        New settings instance
    """
    global _settings
    _settings = Settings()
    return _settings


# Environment configuration helpers
def load_env_file(file_path: str = ".env") -> None:
    """Load environment variables from file.
    
    Args:
        file_path: Path to environment file
    """
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ.setdefault(key.strip(), value.strip())
    except Exception as e:
        print(f"Warning: Could not load environment file {file_path}: {e}")


def get_config_summary() -> Dict[str, Any]:
    """Get configuration summary for debugging.
    
    Returns:
        Configuration summary
    """
    settings = get_settings()
    return {
        "application": {
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "debug": settings.debug
        },
        "server": {
            "host": settings.host,
            "port": settings.port,
            "workers": settings.workers
        },
        "features": {
            "user_registration": settings.feature_user_registration,
            "user_profiles": settings.feature_user_profiles
        },
        "api": {
            "prefix": settings.api_prefix,
            "docs_enabled": settings.docs_url is not None
        }
    }