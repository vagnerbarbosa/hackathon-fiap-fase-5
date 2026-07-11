"""Tests for configuration module."""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from src.core.config import Settings, get_settings


class TestSettings:
    """Test Settings configuration."""

    def test_settings_required_database_url(self):
        """Settings should require DATABASE_URL."""
        # Remove DATABASE_URL from environment
        env_vars = os.environ.copy()
        env_vars.pop("DATABASE_URL", None)

        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()

            assert "database_url" in str(exc_info.value)

    def test_settings_with_required_values(self):
        """Settings should work with required values."""
        settings = Settings(
            database_url="postgresql+asyncpg://user:pass@localhost/db",
            api_key="test-key",
        )

        assert settings.database_url == "postgresql+asyncpg://user:pass@localhost/db"
        assert settings.api_key == "test-key"

    def test_settings_defaults(self):
        """Settings should have correct defaults."""
        settings = Settings(
            database_url="postgresql+asyncpg://user:pass@localhost/db",
            api_key="test-key",
        )

        assert settings.app_name == "FIAP STRIDE API"
        assert settings.app_version == "0.1.0"
        assert settings.debug is False
        assert settings.api_rate_limit == 60
        assert settings.log_level == "INFO"

    def test_settings_api_rate_limit_validation(self):
        """API rate limit should be at least 1."""
        with pytest.raises(ValidationError):
            Settings(
                database_url="postgresql+asyncpg://user:pass@localhost/db",
                api_key="test-key",
                api_rate_limit=0,
            )

    def test_settings_log_level_validation(self):
        """Log level should be one of allowed values."""
        with pytest.raises(ValidationError):
            Settings(
                database_url="postgresql+asyncpg://user:pass@localhost/db",
                api_key="test-key",
                log_level="INVALID",
            )

    def test_get_settings_caches_result(self):
        """get_settings should cache the result."""
        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

    def test_cors_origins_parsing(self):
        """CORS origins should be parsed from comma-separated string."""
        settings = Settings(
            database_url="postgresql+asyncpg://user:pass@localhost/db",
            api_key="test-key",
            cors_origins="http://localhost:3000,http://localhost:8080",
        )

        assert settings.cors_origins == ["http://localhost:3000", "http://localhost:8080"]

    def test_cors_origins_empty(self):
        """CORS origins should default to empty list."""
        settings = Settings(
            database_url="postgresql+asyncpg://user:pass@localhost/db",
            api_key="test-key",
        )

        assert settings.cors_origins == []
