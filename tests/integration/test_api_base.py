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
        """Docs endpoint should be available in debug mode."""
        response = await async_client.get("/docs")
        assert response.status_code == 200

    async def test_threat_model_placeholders(self, async_client: AsyncClient):
        """Threat model endpoints should return placeholder responses."""
        response = await async_client.post("/api/v1/threat-model/analyze")
        assert response.status_code == 202

        data = response.json()
        assert "message" in data
        assert "placeholder" in data["message"].lower()

    async def test_threat_model_get_status(self, async_client: AsyncClient):
        """Threat model status endpoint should work."""
        import uuid

        job_id = uuid.uuid4()
        response = await async_client.get(f"/api/v1/threat-model/{job_id}")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    async def test_threat_model_get_report(self, async_client: AsyncClient):
        """Threat model report endpoint should work."""
        import uuid

        job_id = uuid.uuid4()
        response = await async_client.get(
            f"/api/v1/threat-model/{job_id}/report?format=json"
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data


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
        from httpx import AsyncClient as HttpxAsyncClient
        from src.api.main import app

        async with HttpxAsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/threat-model/analyze")
            assert response.status_code == 401
