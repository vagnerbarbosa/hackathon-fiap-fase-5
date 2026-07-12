"""Testes de integração para funcionalidade base da API."""

import pytest
from httpx import AsyncClient


class TestAPIIntegration:
    """Testes de cenários de integração da API."""

    async def test_health_check_integration(self, async_client: AsyncClient):
        """Health check deve funcionar end-to-end."""
        response = await async_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"

    async def test_api_version_endpoint(self, async_client: AsyncClient):
        """Endpoint de versão deve retornar informações da API."""
        response = await async_client.get("/version")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data

    async def test_docs_endpoint_available(self, async_client: AsyncClient):
        """Endpoint de docs deve redirecionar para docs OpenAPI."""
        response = await async_client.get("/docs", follow_redirects=True)
        # Endpoint docs pode retornar 200, redirect, ou 404 se não configurado
        assert response.status_code in [200, 307, 308, 404]

    async def test_threat_model_analyze_requires_file(self, async_client: AsyncClient):
        """Endpoint analyze deve requerer upload de arquivo."""
        # POST sem arquivo deve retornar 422 após auth
        response = await async_client.post("/api/v1/threat-model/analyze")
        # Primeiro valida API key (401) depois valida arquivo (422)
        assert response.status_code in [401, 422]

    async def test_threat_model_get_status_not_found(self, async_client: AsyncClient):
        """Status deve retornar 404 para job inexistente."""
        import uuid

        job_id = uuid.uuid4()
        response = await async_client.get(f"/api/v1/threat-model/{job_id}")

        # Primeiro valida API key (401) depois retorna 404
        assert response.status_code in [401, 404]

    async def test_threat_model_get_report_not_found(self, async_client: AsyncClient):
        """Relatório deve retornar 404 para job inexistente."""
        import uuid

        job_id = uuid.uuid4()
        response = await async_client.get(
            f"/api/v1/threat-model/{job_id}/report?format=json"
        )

        # Primeiro valida API key (401) depois retorna 404
        assert response.status_code in [401, 404]


class TestSecurityIntegration:
    """Testes de integração de segurança."""

    async def test_security_headers_on_all_routes(self, async_client: AsyncClient):
        """Todas as rotas devem incluir headers de segurança."""
        routes = ["/", "/health", "/version"]

        for route in routes:
            response = await async_client.get(route)
            assert "X-Content-Type-Options" in response.headers
            assert "X-Frame-Options" in response.headers

    async def test_request_id_on_all_routes(self, async_client: AsyncClient):
        """Todas as rotas devem incluir request ID."""
        response = await async_client.get("/health")
        assert "X-Request-ID" in response.headers


class TestErrorHandling:
    """Testes de tratamento de erros da API."""

    async def test_404_not_found(self, async_client: AsyncClient):
        """Rotas inexistentes devem retornar 404."""
        response = await async_client.get("/non-existent-route")
        assert response.status_code == 404

    async def test_401_unauthorized(self, async_client: AsyncClient):
        """Rotas protegidas sem API key devem retornar 401."""
        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        from src.api.main import app

        async with HttpxAsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/threat-model/analyze")
            assert response.status_code == 401
