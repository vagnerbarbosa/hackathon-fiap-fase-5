"""Tests for health check endpoint."""

import pytest
from httpx import AsyncClient


class TestHealthCheck:
    """Test health check endpoint."""

    async def test_health_returns_200(self, async_client: AsyncClient):
        """Health check should return 200 when database is connected."""
        response = await async_client.get("/health")
        assert response.status_code == 200

    async def test_health_response_structure(self, async_client: AsyncClient):
        """Health check should return expected JSON structure."""
        response = await async_client.get("/health")
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert "database" in data
        assert "timestamp" in data

    async def test_health_status_healthy(self, async_client: AsyncClient):
        """Health check should report status as healthy."""
        response = await async_client.get("/health")
        data = response.json()

        assert data["status"] == "healthy"
        assert data["database"] == "connected"

    async def test_health_version_matches(self, async_client: AsyncClient):
        """Health check should return correct API version."""
        response = await async_client.get("/health")
        data = response.json()

        assert data["version"] == "0.1.0"

    async def test_health_without_api_key(self, async_client: AsyncClient):
        """Health check should be accessible without API key."""
        # Create client without API key
        from httpx import AsyncClient as HttpxAsyncClient
        from src.api.main import app

        async with HttpxAsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200

    async def test_root_endpoint(self, async_client: AsyncClient):
        """Root endpoint should return basic info."""
        response = await async_client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
