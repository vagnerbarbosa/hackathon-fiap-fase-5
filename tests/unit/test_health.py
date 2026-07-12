"""Testes para endpoint de health check."""

import pytest
from httpx import AsyncClient


class TestHealthCheck:
    """Testes para endpoint de health check."""

    async def test_health_returns_200(self, async_client: AsyncClient):
        """Health check deve retornar 200 quando database está conectado."""
        response = await async_client.get("/health")
        assert response.status_code == 200

    async def test_health_response_structure(self, async_client: AsyncClient):
        """Health check deve retornar estrutura JSON esperada."""
        response = await async_client.get("/health")
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert "database" in data
        assert "timestamp" in data

    async def test_health_status_healthy(self, async_client: AsyncClient):
        """Health check deve reportar status como healthy."""
        response = await async_client.get("/health")
        data = response.json()

        assert data["status"] == "healthy"
        assert data["database"] == "connected"

    async def test_health_version_matches(self, async_client: AsyncClient):
        """Health check deve retornar versão correta da API."""
        response = await async_client.get("/health")
        data = response.json()

        assert data["version"] == "0.2.0"

    async def test_health_without_api_key(self, async_client: AsyncClient):
        """Health check deve ser acessível sem API key."""
        # Cria client sem API key
        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        from src.api.main import app

        async with HttpxAsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/health")
            assert response.status_code == 200

    async def test_root_endpoint(self, async_client: AsyncClient):
        """Endpoint raiz deve retornar informações básicas."""
        response = await async_client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
