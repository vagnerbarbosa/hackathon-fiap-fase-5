"""Utilitários de segurança: rate limiting, headers, validação de arquivos."""

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
    """Obtém ou cria instância do rate limiter."""
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
    """Adiciona headers de segurança OWASP em todas as respostas."""

    async def dispatch(self, request: Request, call_next: Callable):
        """Adiciona headers de segurança na resposta."""
        response = await call_next(request)

        # OWASP security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )

        # Content-Security-Policy: allow CDN resources in debug mode for Swagger
        if settings.debug:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net unpkg.com; "
                "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
                "img-src 'self' data: cdn.jsdelivr.net fastapi.tiangolo.com; "
                "font-src 'self' cdn.jsdelivr.net; "
                "connect-src 'self'"
            )
        else:
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
    """Adiciona ID de requisição em todas as requisições para rastreamento."""

    async def dispatch(self, request: Request, call_next: Callable):
        """Adiciona ID de requisição ao estado e logs."""
        import uuid

        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Add to response headers
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response


def setup_security(app: FastAPI) -> None:
    """Configura middleware e handlers de segurança para aplicação FastAPI.

    Args:
        app: Instância da aplicação FastAPI.
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
    """Valida tipo de arquivo usando magic bytes.

    Args:
        content: Conteúdo do arquivo em bytes.

    Returns:
        str: Tipo MIME detectado.

    Raises:
        HTTPException: Se o tipo de arquivo não for permitido.
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
    """Valida tamanho do arquivo.

    Args:
        content: Conteúdo do arquivo em bytes.

    Raises:
        HTTPException: Se o arquivo exceder o tamanho máximo.
    """
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds {MAX_FILE_SIZE // (1024 * 1024)}MB limit",
        )


def sanitize_filename(filename: str) -> str:
    """Sanitiza nome de arquivo para prevenir path traversal.

    Args:
        filename: Nome do arquivo original.

    Returns:
        str: Nome do arquivo sanitizado.
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
    """Valida conteúdo e nome do arquivo enviado.

    Args:
        content: Conteúdo do arquivo em bytes.
        filename: Nome do arquivo original.

    Returns:
        tuple: (nome_sanitizado, tipo_mime)

    Raises:
        HTTPException: Se a validação falhar.
    """
    # Validate size
    validate_file_size(content)

    # Validate type
    mime_type = validate_file_type(content)

    # Sanitize filename
    safe_filename = sanitize_filename(filename)

    logger.info(
        "File validated",
        extra={
            "original_filename": filename,
            "safe_filename": safe_filename,
            "mime_type": mime_type,
            "size": len(content),
        },
    )

    return safe_filename, mime_type
