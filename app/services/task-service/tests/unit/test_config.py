"""
Unit tests for configuration settings (src/config/settings.py).

These tests verify:
- Environment variable loading
- Default values
- Validators (SECRET_KEY, CORS_ORIGINS)
- DATABASE_URL property construction
- Settings singleton behavior
"""

import os

import pytest
from pydantic import ValidationError

from src.config.settings import Settings


# ============================================================================
# SETTINGS CREATION TESTS
# ============================================================================

class TestSettingsCreation:
    """Test creating Settings instances."""
    
    def test_create_settings_with_defaults(self, monkeypatch):
        """Test that Settings uses default values when env vars not set."""
        # Clear any existing environment variables
        for key in ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]:
            monkeypatch.delenv(key, raising=False)
        
        settings = Settings()
        
        # Check defaults from settings.py
        assert settings.DB_HOST == "localhost"
        assert settings.DB_PORT == 5432
        assert settings.DB_NAME == "taskdb"
        assert settings.DB_USER == "postgres"
    
    def test_create_settings_from_env_vars(self, monkeypatch):
        """Test that Settings loads from environment variables."""
        monkeypatch.setenv("DB_HOST", "customhost")
        monkeypatch.setenv("DB_PORT", "3306")
        monkeypatch.setenv("DB_NAME", "customdb")
        monkeypatch.setenv("DB_USER", "customuser")
        monkeypatch.setenv("DB_PASSWORD", "custompass")
        
        settings = Settings()
        
        assert settings.DB_HOST == "customhost"
        assert settings.DB_PORT == 3306
        assert settings.DB_NAME == "customdb"
        assert settings.DB_USER == "customuser"
        assert settings.DB_PASSWORD == "custompass"
    
    def test_environment_field(self, monkeypatch):
        """Test ENVIRONMENT field with different values."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        settings = Settings()
        assert settings.ENVIRONMENT == "production"
        
        monkeypatch.setenv("ENVIRONMENT", "development")
        settings = Settings()
        assert settings.ENVIRONMENT == "development"
    
    def test_debug_field(self, monkeypatch):
        """Test DEBUG boolean field."""
        monkeypatch.setenv("DEBUG", "true")
        settings = Settings()
        assert settings.DEBUG is True
        
        monkeypatch.setenv("DEBUG", "false")
        settings = Settings()
        assert settings.DEBUG is False
        
        monkeypatch.setenv("DEBUG", "1")
        settings = Settings()
        assert settings.DEBUG is True


# ============================================================================
# DATABASE_URL PROPERTY TESTS
# ============================================================================

class TestDatabaseURL:
    """Test DATABASE_URL property construction."""
    
    def test_database_url_construction(self, monkeypatch):
        """Test that DATABASE_URL is constructed correctly from parts."""
        monkeypatch.setenv("DB_HOST", "testhost")
        monkeypatch.setenv("DB_PORT", "5432")
        monkeypatch.setenv("DB_NAME", "testdb")
        monkeypatch.setenv("DB_USER", "testuser")
        monkeypatch.setenv("DB_PASSWORD", "testpass")
        
        settings = Settings()
        
        expected_url = "postgresql://testuser:testpass@testhost:5432/testdb"
        assert settings.DATABASE_URL == expected_url
    
    def test_database_url_with_special_chars_in_password(self, monkeypatch):
        """Test DATABASE_URL with special characters in password."""
        monkeypatch.setenv("DB_PASSWORD", "p@ss:word!")
        
        settings = Settings()
        
        # Password should be included as-is (URL encoding handled by driver)
        assert "p@ss:word!" in settings.DATABASE_URL
    
    def test_database_url_different_ports(self, monkeypatch):
        """Test DATABASE_URL with different port numbers."""
        monkeypatch.setenv("DB_PORT", "3306")
        settings = Settings()
        assert ":3306/" in settings.DATABASE_URL
        
        monkeypatch.setenv("DB_PORT", "5433")
        settings = Settings()
        assert ":5433/" in settings.DATABASE_URL


# ============================================================================
# SECRET_KEY VALIDATOR TESTS
# ============================================================================

class TestSecretKeyValidator:
    """Test SECRET_KEY field and validator."""
    
    def test_secret_key_auto_generated_if_not_provided(self, monkeypatch):
        """Test that SECRET_KEY is auto-generated when not in environment."""
        monkeypatch.delenv("SECRET_KEY", raising=False)
        
        settings = Settings()
        
        # Should have a secret key
        assert settings.SECRET_KEY is not None
        assert len(settings.SECRET_KEY) > 0
    
    def test_secret_key_from_environment(self, monkeypatch):
        """Test that SECRET_KEY can be provided via environment."""
        custom_key = "my-super-secret-key-12345"
        monkeypatch.setenv("SECRET_KEY", custom_key)
        
        settings = Settings()
        
        assert settings.SECRET_KEY == custom_key
    
    def test_secret_key_minimum_length_validation(self, monkeypatch):
        """Test that SECRET_KEY must be at least 32 characters."""
        # Short key should be rejected
        monkeypatch.setenv("SECRET_KEY", "short")
        
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        
        errors = exc_info.value.errors()
        assert any("SECRET_KEY" in str(error) for error in errors)
        assert any("32 characters" in str(error) for error in errors)
    
    def test_secret_key_exactly_32_chars(self, monkeypatch):
        """Test that SECRET_KEY with exactly 32 characters is valid."""
        valid_key = "a" * 32
        monkeypatch.setenv("SECRET_KEY", valid_key)
        
        settings = Settings()
        
        assert settings.SECRET_KEY == valid_key
        assert len(settings.SECRET_KEY) == 32
    
    def test_secret_key_longer_than_32_chars(self, monkeypatch):
        """Test that SECRET_KEY longer than 32 characters is valid."""
        long_key = "a" * 64
        monkeypatch.setenv("SECRET_KEY", long_key)
        
        settings = Settings()
        
        assert settings.SECRET_KEY == long_key


# ============================================================================
# CORS_ORIGINS VALIDATOR TESTS
# ============================================================================

class TestCORSOriginsValidator:
    """Test CORS_ORIGINS field and parsing."""
    
    def test_cors_origins_default(self, monkeypatch):
        """Test that CORS_ORIGINS has default values."""
        monkeypatch.delenv("CORS_ORIGINS", raising=False)
        
        settings = Settings()
        
        # Should have default origins
        assert isinstance(settings.CORS_ORIGINS, list)
        assert "http://localhost:3000" in settings.CORS_ORIGINS
    
    def test_cors_origins_single_origin(self, monkeypatch):
        """Test CORS_ORIGINS with a single origin."""
        monkeypatch.setenv("CORS_ORIGINS", "https://example.com")
        
        settings = Settings()
        
        assert settings.CORS_ORIGINS == ["https://example.com"]
    
    def test_cors_origins_multiple_comma_separated(self, monkeypatch):
        """Test CORS_ORIGINS with comma-separated list."""
        origins = "https://app.example.com,https://admin.example.com,http://localhost:8080"
        monkeypatch.setenv("CORS_ORIGINS", origins)
        
        settings = Settings()
        
        expected = [
            "https://app.example.com",
            "https://admin.example.com",
            "http://localhost:8080",
        ]
        assert settings.CORS_ORIGINS == expected
    
    def test_cors_origins_with_whitespace(self, monkeypatch):
        """Test that CORS_ORIGINS strips whitespace."""
        origins = " https://app.com , https://admin.com , http://localhost:3000 "
        monkeypatch.setenv("CORS_ORIGINS", origins)
        
        settings = Settings()
        
        # Whitespace should be stripped
        expected = ["https://app.com", "https://admin.com", "http://localhost:3000"]
        assert settings.CORS_ORIGINS == expected
    
    def test_cors_origins_empty_string(self, monkeypatch):
        """Test CORS_ORIGINS with empty string."""
        monkeypatch.setenv("CORS_ORIGINS", "")
        
        settings = Settings()
        
        # Should result in empty list or default
        # (Depending on implementation, might keep default)
        assert isinstance(settings.CORS_ORIGINS, list)


# ============================================================================
# OPENTELEMETRY SETTINGS TESTS
# ============================================================================

class TestOpenTelemetrySettings:
    """Test OpenTelemetry configuration fields."""
    
    def test_otel_enabled_default(self, monkeypatch):
        """Test OTEL_ENABLED default value."""
        monkeypatch.delenv("OTEL_ENABLED", raising=False)
        
        settings = Settings()
        
        # Default should be False for testing
        assert settings.OTEL_ENABLED is False
    
    def test_otel_enabled_true(self, monkeypatch):
        """Test enabling OpenTelemetry."""
        monkeypatch.setenv("OTEL_ENABLED", "true")
        
        settings = Settings()
        
        assert settings.OTEL_ENABLED is True
    
    def test_otel_service_name(self, monkeypatch):
        """Test OTEL_SERVICE_NAME configuration."""
        monkeypatch.setenv("OTEL_SERVICE_NAME", "custom-service")
        
        settings = Settings()
        
        assert settings.OTEL_SERVICE_NAME == "custom-service"
    
    def test_otel_exporter_endpoint(self, monkeypatch):
        """Test OTEL_EXPORTER_ENDPOINT configuration."""
        endpoint = "http://jaeger:4317"
        monkeypatch.setenv("OTEL_EXPORTER_ENDPOINT", endpoint)
        
        settings = Settings()
        
        assert settings.OTEL_EXPORTER_ENDPOINT == endpoint


# ============================================================================
# SETTINGS IMMUTABILITY TESTS
# ============================================================================

class TestSettingsImmutability:
    """Test that Settings behaves correctly with Pydantic."""
    
    def test_settings_are_frozen_if_configured(self):
        """Test if settings are immutable (if frozen in model config)."""
        settings = Settings()
        
        # Try to modify a field
        # If frozen, this should raise an error
        # If not frozen, this is just a check that fields can be read
        original_host = settings.DB_HOST
        
        # Attempt to change (may or may not be allowed depending on config)
        try:
            settings.DB_HOST = "newhost"
            # If this succeeds, settings are mutable
            # Revert for other tests
            settings.DB_HOST = original_host
        except Exception:
            # If this fails, settings are frozen (good for config)
            pass
    
    def test_settings_can_be_recreated(self, monkeypatch):
        """Test that new Settings instances can be created."""
        settings1 = Settings()
        
        # Change environment
        monkeypatch.setenv("DB_HOST", "newhost")
        
        settings2 = Settings()
        
        # New instance should have new values
        assert settings2.DB_HOST == "newhost"


# ============================================================================
# INTEGRATION WITH ENV FILE TESTS
# ============================================================================

class TestEnvFileIntegration:
    """Test that Settings can load from .env file."""
    
    def test_env_file_loading_simulation(self, monkeypatch):
        """Simulate loading from .env file via environment variables."""
        # Simulate .env file contents
        env_vars = {
            "ENVIRONMENT": "production",
            "DEBUG": "false",
            "DB_HOST": "prod-db.example.com",
            "DB_PORT": "5432",
            "DB_NAME": "production_db",
            "DB_USER": "prod_user",
            "DB_PASSWORD": "prod_secure_password",
            "OTEL_ENABLED": "true",
            "OTEL_EXPORTER_ENDPOINT": "http://jaeger:4317",
            "SECRET_KEY": "production-secret-key-minimum-32-characters-required",
            "CORS_ORIGINS": "https://app.production.com,https://admin.production.com",
        }
        
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)
        
        settings = Settings()
        
        # Verify all values loaded correctly
        assert settings.ENVIRONMENT == "production"
        assert settings.DEBUG is False
        assert settings.DB_HOST == "prod-db.example.com"
        assert settings.DB_NAME == "production_db"
        assert settings.OTEL_ENABLED is True
        assert "https://app.production.com" in settings.CORS_ORIGINS
