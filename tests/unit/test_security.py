"""Tests for security utilities."""

import pytest
from fastapi import HTTPException

from src.core.security import (
    sanitize_filename,
    validate_file_size,
)


class TestSecurityUtils:
    """Test security utility functions."""

    def test_sanitize_filename_removes_path_traversal(self):
        """Sanitize should remove path traversal attempts."""
        assert sanitize_filename("../../../etc/passwd") == "passwd"

    def test_sanitize_filename_removes_backslashes(self):
        """Sanitize should remove backslashes."""
        assert sanitize_filename("..\\..\\windows\\system32") == "windows" + "system32"

    def test_sanitize_filename_limits_length(self):
        """Sanitize should limit filename length."""
        long_name = "a" * 300 + ".txt"
        result = sanitize_filename(long_name)
        assert len(result) <= 255

    def test_sanitize_filename_keeps_safe_names(self):
        """Sanitize should keep safe filenames."""
        assert sanitize_filename("image.png") == "image.png"
        assert sanitize_filename("file_name-123.jpg") == "file_name-123.jpg"

    def test_validate_file_size_accepts_small_files(self):
        """Validation should accept files under max size."""
        content = b"x" * (50 * 1024 * 1024 - 1)  # Just under 50MB
        validate_file_size(content)  # Should not raise

    def test_validate_file_size_rejects_large_files(self):
        """Validation should reject files over max size."""
        content = b"x" * (50 * 1024 * 1024 + 1)  # Just over 50MB

        with pytest.raises(HTTPException) as exc_info:
            validate_file_size(content)

        assert exc_info.value.status_code == 413


class TestSecurityHeaders:
    """Test security headers middleware."""

    async def test_security_headers_present(self, async_client):
        """Response should include security headers."""
        response = await async_client.get("/health")

        assert response.status_code == 200

        headers = response.headers
        assert headers.get("X-Content-Type-Options") == "nosniff"
        assert headers.get("X-Frame-Options") == "DENY"
        assert headers.get("X-XSS-Protection") == "1; mode=block"

    async def test_request_id_header_present(self, async_client):
        """Response should include X-Request-ID header."""
        response = await async_client.get("/health")
        assert "X-Request-ID" in response.headers


class TestAPIKeyAuth:
    """Test API Key authentication."""

    async def test_missing_api_key_returns_401(self, async_client):
        """Request without API key should return 401."""
        from httpx import AsyncClient as HttpxAsyncClient
        from src.api.main import app

        async with HttpxAsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/threat-model/analyze")
            assert response.status_code == 401

    async def test_invalid_api_key_returns_401(self, async_client):
        """Request with invalid API key should return 401."""
        from httpx import AsyncClient as HttpxAsyncClient
        from src.api.main import app

        async with HttpxAsyncClient(
            app=app,
            base_url="http://test",
            headers={"X-API-Key": "invalid-key"},
        ) as client:
            response = await client.get("/api/v1/threat-model/analyze")
            assert response.status_code == 401

    async def test_valid_api_key_allows_access(self, async_client):
        """Request with valid API key should succeed."""
        response = await async_client.get("/api/v1/threat-model/analyze")
        # Should not be 401 (endpoint is placeholder, so 202 expected)
        assert response.status_code != 401
