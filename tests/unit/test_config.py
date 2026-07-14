"""Testes para módulo de configuração."""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from src.core.config import Settings, get_settings


class TestSettings:
    """Testes para configuração Settings."""

    def test_settings_required_database_url(self):
        """Settings deve requerer DATABASE_URL."""
        from pydantic_settings import SettingsConfigDict

        # Cria classe de teste que ignora arquivo env
        class TestSettingsRequired(Settings):
            model_config = SettingsConfigDict(env_file=None)

        # Remove DATABASE_URL do ambiente
        env_vars = os.environ.copy()
        env_vars.pop("DATABASE_URL", None)

        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                TestSettingsRequired()

            assert "database_url" in str(exc_info.value)

    def test_settings_with_required_values(self):
        """Settings deve funcionar com valores obrigatórios."""
        settings = Settings(
            database_url="postgresql+asyncpg://user:pass@localhost/db",
            api_key="test-key",
        )

        assert settings.database_url == "postgresql+asyncpg://user:pass@localhost/db"
        assert settings.api_key == "test-key"

    def test_settings_defaults(self):
        """Settings deve ter defaults corretos."""
        settings = Settings(
            database_url="postgresql+asyncpg://user:pass@localhost/db",
            api_key="test-key",
        )

        assert settings.app_name == "FIAP STRIDE API"
        assert settings.app_version == "0.2.0"
        assert settings.debug is False
        assert settings.api_rate_limit == 60
        assert settings.log_level == "INFO"

    def test_settings_api_rate_limit_validation(self):
        """Limite de rate da API deve ser pelo menos 1."""
        with pytest.raises(ValidationError):
            Settings(
                database_url="postgresql+asyncpg://user:pass@localhost/db",
                api_key="test-key",
                api_rate_limit=0,
            )

    def test_settings_log_level_validation(self):
        """Nível de log deve ser um dos valores permitidos."""
        with pytest.raises(ValidationError):
            Settings(
                database_url="postgresql+asyncpg://user:pass@localhost/db",
                api_key="test-key",
                log_level="INVALID",
            )

    def test_get_settings_caches_result(self):
        """get_settings deve cachear o resultado."""
        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

    def test_cors_origins_parsing(self):
        """CORS origins deve ser parseado de string separada por vírgulas."""
        settings = Settings(
            database_url="postgresql+asyncpg://user:pass@localhost/db",
            api_key="test-key",
            cors_origins="http://localhost:3000,http://localhost:8080",
        )

        assert settings.cors_origins == ["http://localhost:3000", "http://localhost:8080"]

    def test_cors_origins_empty(self):
        """CORS origins deve ter lista vazia como default."""
        settings = Settings(
            database_url="postgresql+asyncpg://user:pass@localhost/db",
            api_key="test-key",
        )

        assert settings.cors_origins == []
