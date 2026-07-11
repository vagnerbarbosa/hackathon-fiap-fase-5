"""Endpoint de verificação de saúde da API."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db
from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["health"])


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check API and database health status.",
)
async def health_check(db: AsyncSession = Depends(get_db)) -> dict:
    """Verifica status de saúde da API.

    Returns:
        dict: Informações de status de saúde.

    Response Codes:
        200: API e banco de dados estão saudáveis
        503: Banco de dados indisponível
    """
    # Check database connectivity
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"

    response = {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "version": settings.app_version,
        "database": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Return 503 if database is down
    if db_status == "disconnected":
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=response,
        )

    return response


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="Root endpoint",
    include_in_schema=False,
)
async def root() -> dict:
    """Endpoint raiz que redireciona para documentação."""
    return {
        "message": "FIAP STRIDE API",
        "version": settings.app_version,
        "docs": "/docs",
    }
