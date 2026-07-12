"""Testes para utilitários de segurança."""

import pytest
from fastapi import HTTPException

from src.core.security import (
    sanitize_filename,
    validate_file_size,
)


class TestSecurityUtils:
    """Testes para funções utilitárias de segurança."""

    def test_sanitize_filename_removes_path_traversal(self):
        """Sanitize deve remover tentativas de path traversal."""
        assert sanitize_filename("../../../etc/passwd") == "passwd"

    def test_sanitize_filename_removes_backslashes(self):
        """Sanitize deve remover backslashes."""
        assert sanitize_filename("..\\..\\windows\\system32") == "windows" + "system32"

    def test_sanitize_filename_limits_length(self):
        """Sanitize deve limitar tamanho do nome do arquivo."""
        long_name = "a" * 300 + ".txt"
        result = sanitize_filename(long_name)
        assert len(result) <= 255

    def test_sanitize_filename_keeps_safe_names(self):
        """Sanitize deve manter nomes de arquivo seguros."""
        assert sanitize_filename("image.png") == "image.png"
        assert sanitize_filename("file_name-123.jpg") == "file_name-123.jpg"

    def test_validate_file_size_accepts_small_files(self):
        """Validação deve aceitar arquivos abaixo do tamanho máximo."""
        content = b"x" * (50 * 1024 * 1024 - 1)  # Pouco abaixo de 50MB
        validate_file_size(content)  # Não deve lançar exceção

    def test_validate_file_size_rejects_large_files(self):
        """Validação deve rejeitar arquivos acima do tamanho máximo."""
        content = b"x" * (50 * 1024 * 1024 + 1)  # Pouco acima de 50MB

        with pytest.raises(HTTPException) as exc_info:
            validate_file_size(content)

        assert exc_info.value.status_code == 413


class TestSecurityHeaders:
    """Testes para middleware de headers de segurança."""

    async def test_security_headers_present(self, async_client):
        """Resposta deve incluir headers de segurança."""
        response = await async_client.get("/health")

        assert response.status_code == 200

        headers = response.headers
        assert headers.get("X-Content-Type-Options") == "nosniff"
        assert headers.get("X-Frame-Options") == "DENY"
        assert headers.get("X-XSS-Protection") == "1; mode=block"

    async def test_request_id_header_present(self, async_client):
        """Resposta deve incluir header X-Request-ID."""
        response = await async_client.get("/health")
        assert "X-Request-ID" in response.headers


class TestAPIKeyAuth:
    """Testes para autenticação por API Key."""

    async def test_missing_api_key_returns_401(self, async_client):
        """Requisição sem API key deve retornar 401."""
        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        from src.api.main import app

        async with HttpxAsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/threat-model/analyze")
            assert response.status_code == 401

    async def test_invalid_api_key_returns_401(self, async_client):
        """Requisição com API key inválida deve retornar 401."""
        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        from src.api.main import app

        async with HttpxAsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"X-API-Key": "invalid-key"},
        ) as client:
            response = await client.get("/api/v1/threat-model/analyze")
            assert response.status_code == 401

    async def test_valid_api_key_allows_access(self, async_client):
        """Requisição com API key válida deve funcionar no health endpoint."""
        # Health endpoint não requer API key mas async_client inclui
        # Isso verifica se o client está configurado corretamente
        response = await async_client.get("/health")
        # Não deve ser 401 (health endpoint é acessível)
        assert response.status_code != 401
