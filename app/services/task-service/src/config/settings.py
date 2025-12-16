"""
Task Service - Configuration Settings

Manages all application configuration using Pydantic Settings.
Loads configuration from environment variables and .env file.

This follows the 12-Factor App methodology:
https://12factor.net/config

Author: Krishan Shukla
Date: December 9, 2025
"""

from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Usage:
        from src.config.settings import settings
        
        print(settings.DB_HOST)  # Access configuration
    
    Environment variables are loaded from:
    1. System environment variables
    2. .env file (if exists)
    3. Default values (defined below)
    """
    
    # ========================================================================
    # APPLICATION SETTINGS
    # ========================================================================
    
    APP_NAME: str = Field(
        default="task-service",
        description="Application name"
    )
    
    VERSION: str = Field(
        default="1.0.0",
        description="Application version"
    )
    
    DEBUG: bool = Field(
        default=False,
        description="Enable debug mode (verbose logging, auto-reload)"
    )
    
    ENVIRONMENT: str = Field(
        default="development",
        description="Environment: development, staging, production"
    )
    
    # ========================================================================
    # DATABASE CONFIGURATION
    # ========================================================================
    
    DB_USER: str = Field(
        default="postgres",
        description="PostgreSQL username"
    )
    
    DB_PASSWORD: str = Field(
        default="postgres",
        description="PostgreSQL password"
    )
    
    DB_HOST: str = Field(
        default="localhost",
        description="PostgreSQL host"
    )
    
    DB_PORT: int = Field(
        default=5432,
        description="PostgreSQL port"
    )
    
    DB_NAME: str = Field(
        default="taskdb",
        description="PostgreSQL database name"
    )
    
    @property
    def DATABASE_URL(self) -> str:
        """
        Constructs PostgreSQL connection URL.
        
        Format: postgresql://user:password@host:port/database
        
        Returns:
            str: Complete database connection string
        """
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # ========================================================================
    # OPENTELEMETRY (Observability)
    # ========================================================================
    
    OTEL_ENABLED: bool = Field(
        default=False,
        description="Enable OpenTelemetry tracing"
    )
    
    OTEL_EXPORTER_ENDPOINT: Optional[str] = Field(
        default=None,
        description="OpenTelemetry collector endpoint (e.g., http://localhost:4317)"
    )
    
    OTEL_SERVICE_NAME: str = Field(
        default="task-service",
        description="Service name for tracing"
    )
    
    # ========================================================================
    # SECURITY
    # ========================================================================
    
    SECRET_KEY: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for JWT tokens (min 32 characters)"
    )
    
    ALGORITHM: str = Field(
        default="HS256",
        description="JWT algorithm"
    )
    
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="JWT token expiration time in minutes"
    )
    
    @field_validator("SECRET_KEY")
    def validate_secret_key(cls, v, info):
        """
        Validates that SECRET_KEY is secure enough.
        
        In production, SECRET_KEY must be:
        - At least 32 characters
        - Not the default value
        """
        if info.data.get("ENVIRONMENT") == "production":
            if len(v) < 32:
                raise ValueError("SECRET_KEY must be at least 32 characters in production")
            if v == "dev-secret-key-change-in-production":
                raise ValueError("Must change SECRET_KEY in production!")
        return v
    
    # ========================================================================
    # API CONFIGURATION
    # ========================================================================
    
    API_V1_PREFIX: str = Field(
        default="/api/v1",
        description="API version 1 prefix"
    )
    
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins"
    )
    
    @field_validator("CORS_ORIGINS", mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """
        Parse CORS_ORIGINS from string or list.
        
        Environment variable can be:
        - Comma-separated string: "http://localhost:3000,http://localhost:8080"
        - List: ["http://localhost:3000", "http://localhost:8080"]
        """
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    # ========================================================================
    # LOGGING
    # ========================================================================
    
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )
    
    LOG_FORMAT: str = Field(
        default="json",  # Options: json, text
        description="Log format"
    )
    
    SHOW_SQL_QUERIES: bool = Field(
        default=False,
        description="Show SQL queries in logs (useful for debugging)"
    )
    
    # ========================================================================
    # PYDANTIC CONFIGURATION
    # ========================================================================
    
    class Config:
        """
        Pydantic configuration.
        
        - env_file: Load from .env file
        - case_sensitive: Environment variables are case-sensitive
        - validate_assignment: Validate on assignment (not just initialization)
        """
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        validate_assignment = True
        
        # Allow extra fields (for future compatibility)
        extra = "allow"


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================
# Create a single instance of Settings that's imported everywhere
# This ensures configuration is loaded once and reused

settings = Settings()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_settings() -> Settings:
    """
    Returns the settings instance.
    
    Useful for dependency injection in FastAPI:
    
    @app.get("/info")
    async def info(settings: Settings = Depends(get_settings)):
        return {"db_host": settings.DB_HOST}
    """
    return settings


# ============================================================================
# DISPLAY CONFIGURATION (for debugging)
# ============================================================================

def display_settings():
    """
    Prints current configuration (hiding sensitive values).
    Useful for debugging and verifying configuration.
    """
    print("=" * 60)
    print("⚙️  Configuration Settings")
    print("=" * 60)
    print(f"App Name:     {settings.APP_NAME}")
    print(f"Version:      {settings.VERSION}")
    print(f"Environment:  {settings.ENVIRONMENT}")
    print(f"Debug Mode:   {settings.DEBUG}")
    print("-" * 60)
    print(f"DB Host:      {settings.DB_HOST}")
    print(f"DB Port:      {settings.DB_PORT}")
    print(f"DB Name:      {settings.DB_NAME}")
    print(f"DB User:      {settings.DB_USER}")
    print(f"DB Password:  {'*' * len(settings.DB_PASSWORD)} (hidden)")
    print("-" * 60)
    print(f"OTEL Enabled: {settings.OTEL_EXPORTER_OTLP_ENDPOINT is not None}")
    print(f"OTEL Service: {settings.OTEL_SERVICE_NAME}")
    print("-" * 60)
    print(f"CORS Origins: {settings.CORS_ORIGINS}")
    print(f"Log Level:    {settings.LOG_LEVEL}")
    print("=" * 60)


# ============================================================================
# RUN THIS FILE TO TEST CONFIGURATION
# ============================================================================

if __name__ == "__main__":
    # Test configuration loading
    display_settings()
    
    # Test database URL construction
    print("\n📊 Database URL:")
    # Don't print actual URL (contains password)
    print(f"postgresql://{settings.DB_USER}:***@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
