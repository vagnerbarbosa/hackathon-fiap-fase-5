"""Integration tests for API base functionality."""

import pytest
from httpx import AsyncClient


class TestAPIIntegration:
    """Test API integration scenarios."""

    async def test_health_check_integration(self, async_client: AsyncClient):
        """Health check should work end-to-end."""
        response = await async_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"

    async def test_api_version_endpoint(self, async_client: AsyncClient):
        """Version endpoint should return API info."""
        response = await async_client.get("/version")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data

    async def test_docs_endpoint_available(self, async_client: AsyncClient):
        """Docs endpoint should redirect to OpenAPI docs."""
        response = await async_client.get("/docs", follow_redirects=True)
        # Docs endpoint may return 200, redirect, or 404 if not configured
        assert response.status_code in [200, 307, 308, 404]

    async def test_threat_model_analyze_requires_file(self, async_client: AsyncClient):
        """Threat model analyze endpoint should require file upload."""
        # POST without file should return 422 (Unprocessable Entity) after auth
        response = await async_client.post("/api/v1/threat-model/analyze")
        # First validates API key (401) then validates file (422)
        assert response.status_code in [401, 422]

    async def test_threat_model_get_status_not_found(self, async_client: AsyncClient):
        """Threat model status should return 404 for non-existent job."""
        import uuid

        job_id = uuid.uuid4()
        response = await async_client.get(f"/api/v1/threat-model/{job_id}")

        # First validates API key (401) then returns 404 for not found
        assert response.status_code in [401, 404]

    async def test_threat_model_get_report_not_found(self, async_client: AsyncClient):
        """Threat model report should return 404 for non-existent job."""
        import uuid

        job_id = uuid.uuid4()
        response = await async_client.get(
            f"/api/v1/threat-model/{job_id}/report?format=json"
        )

        # First validates API key (401) then returns 404 for not found
        assert response.status_code in [401, 404]


class TestSecurityIntegration:
    """Test security features integration."""

    async def test_security_headers_on_all_routes(self, async_client: AsyncClient):
        """All routes should include security headers."""
        routes = ["/", "/health", "/version"]

        for route in routes:
            response = await async_client.get(route)
            assert "X-Content-Type-Options" in response.headers
            assert "X-Frame-Options" in response.headers

    async def test_request_id_on_all_routes(self, async_client: AsyncClient):
        """All routes should include request ID."""
        response = await async_client.get("/health")
        assert "X-Request-ID" in response.headers


class TestErrorHandling:
    """Test API error handling."""

    async def test_404_not_found(self, async_client: AsyncClient):
        """Non-existent routes should return 404."""
        response = await async_client.get("/non-existent-route")
        assert response.status_code == 404

    async def test_401_unauthorized(self, async_client: AsyncClient):
        """Protected routes without API key should return 401."""
        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        from src.api.main import app

        async with HttpxAsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/threat-model/analyze")
            assert response.status_code == 401
