"""Security utilities: rate limiting, headers, file validation."""

import logging
from pathlib import Path
from typing import Callable, Optional

import magic
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)

# Initialize rate limiter with Redis if available, fallback to memory
limiter: Optional[Limiter] = None


def get_limiter() -> Limiter:
    """Get or create rate limiter instance."""
    global limiter
    if limiter is None:
        try:
            # Try Redis backend first
            limiter = Limiter(
                key_func=get_remote_address,
                default_limits=[f"{settings.api_rate_limit} per minute"],
                storage_uri=settings.redis_url,
            )
            logger.info("Rate limiter initialized with Redis backend")
        except Exception as e:
            # Fallback to memory backend
            logger.warning(
                f"Redis unavailable for rate limiting: {e}. Using in-memory fallback."
            )
            limiter = Limiter(
                key_func=get_remote_address,
                default_limits=[f"{settings.api_rate_limit} per minute"],
                storage_uri="memory://",
            )
            logger.info("Rate limiter initialized with in-memory backend")
    return limiter


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add OWASP security headers to all responses."""

    async def dispatch(self, request: Request, call_next: Callable):
        """Add security headers to response."""
        response = await call_next(request)

        # OWASP security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        return response


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Add request ID to all requests for tracing."""

    async def dispatch(self, request: Request, call_next: Callable):
        """Add request ID to request state and logs."""
        import uuid

        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Add to response headers
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response


def setup_security(app: FastAPI) -> None:
    """Configure security middleware and handlers for FastAPI app.

    Args:
        app: FastAPI application instance.
    """
    # Add security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)

    # Add request ID middleware
    app.add_middleware(RequestIdMiddleware)

    # Configure rate limiter
    limiter = get_limiter()
    app.state.limiter = limiter
    app.add_exception_handler(
        RateLimitExceeded,
        lambda req, exc: JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Rate limit exceeded"},
            headers={"Retry-After": "60"},
        ),
    )

    logger.info("Security middleware configured")


# File validation constants
ALLOWED_MIME_TYPES = {
    "image/png": ["png"],
    "image/jpeg": ["jpg", "jpeg"],
    "image/jpg": ["jpg", "jpeg"],
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def validate_file_type(content: bytes) -> str:
    """Validate file type using magic bytes.

    Args:
        content: File content as bytes.

    Returns:
        str: Detected MIME type.

    Raises:
        HTTPException: If file type is not allowed.
    """
    try:
        detected = magic.from_buffer(content, mime=True)
    except Exception as e:
        logger.error(f"Failed to detect file type: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not determine file type",
        )

    if detected not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{detected}' not allowed. Allowed: PNG, JPEG",
        )

    return detected


def validate_file_size(content: bytes) -> None:
    """Validate file size.

    Args:
        content: File content as bytes.

    Raises:
        HTTPException: If file exceeds maximum size.
    """
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds {MAX_FILE_SIZE // (1024 * 1024)}MB limit",
        )


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal.

    Args:
        filename: Original filename.

    Returns:
        str: Sanitized filename.
    """
    # Remove path components
    safe = Path(filename).name

    # Remove potentially dangerous characters
    safe = safe.replace("..", "").replace("/", "").replace("\\", "")

    # Limit length
    if len(safe) > 255:
        safe = safe[:255]

    return safe


def validate_upload_file(content: bytes, filename: str) -> tuple[str, str]:
    """Validate uploaded file content and name.

    Args:
        content: File content as bytes.
        filename: Original filename.

    Returns:
        tuple: (sanitized_filename, mime_type)

    Raises:
        HTTPException: If validation fails.
    """
    # Validate size
    validate_file_size(content)

    # Validate type
    mime_type = validate_file_type(content)

    # Sanitize filename
    safe_filename = sanitize_filename(filename)

    logger.info(
        "File validated",
        extra_fields={
            "original_filename": filename,
            "safe_filename": safe_filename,
            "mime_type": mime_type,
            "size": len(content),
        },
    )

    return safe_filename, mime_type
