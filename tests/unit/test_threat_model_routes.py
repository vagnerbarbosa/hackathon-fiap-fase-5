"""Tests for threat model API routes."""

import pytest
from httpx import AsyncClient


class TestThreatModelAuth:
    """Test authentication on threat model endpoints."""

    async def test_analyze_requires_api_key(self, async_client: AsyncClient):
        """Should return 401 without API key."""
        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        from src.api.main import app

        async with HttpxAsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/threat-model/analyze")
            assert response.status_code == 401

    async def test_get_status_requires_api_key(self, async_client: AsyncClient):
        """Should return 401 without API key."""
        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        from src.api.main import app
        from uuid import uuid4

        async with HttpxAsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(f"/api/v1/threat-model/{uuid4()}")
            assert response.status_code == 401

    async def test_get_report_requires_api_key(self, async_client: AsyncClient):
        """Should return 401 without API key."""
        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        from src.api.main import app
        from uuid import uuid4

        async with HttpxAsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(f"/api/v1/threat-model/{uuid4()}/report")
            assert response.status_code == 401


class TestThreatModelResponses:
    """Test threat model endpoint responses."""

    async def test_status_returns_json(self, async_client: AsyncClient):
        """Status endpoint should return JSON."""
        from uuid import uuid4

        response = await async_client.get(f"/api/v1/threat-model/{uuid4()}")
        assert response.headers.get("content-type") == "application/json"

    async def test_report_returns_json(self, async_client: AsyncClient):
        """Report endpoint should return JSON."""
        from uuid import uuid4

        response = await async_client.get(f"/api/v1/threat-model/{uuid4()}/report")
        assert response.headers.get("content-type") == "application/json"

    async def test_analyze_accepts_png(self, async_client: AsyncClient):
        """Should accept PNG files."""
        from io import BytesIO

        fake_png = BytesIO(b"\x89PNG\r\n\x1a\n" + b"fake content")
        files = {"file": ("diagram.png", fake_png, "image/png")}

        response = await async_client.post(
            "/api/v1/threat-model/analyze",
            files=files
        )

        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "processing"

    async def test_analyze_rejects_text(self, async_client: AsyncClient):
        """Should reject text files."""
        from io import BytesIO

        files = {"file": ("test.txt", BytesIO(b"content"), "text/plain")}
        response = await async_client.post(
            "/api/v1/threat-model/analyze",
            files=files
        )

        assert response.status_code == 400
