"""FastAPI dependency injection providers."""

from typing import Annotated, AsyncGenerator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings, get_settings, settings
from src.core.logging import get_logger
from src.infrastructure.database import AsyncSessionLocal, test_connection
from src.infrastructure.storage import LocalFileStorage

logger = get_logger(__name__)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide database session dependency.

    Yields:
        AsyncSession: Database session.

    Example:
        @app.get("/items")
        async def get_items(db: SessionDep):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_storage() -> LocalFileStorage:
    """Provide file storage dependency.

    Returns:
        LocalFileStorage: Storage service instance.
    """
    return LocalFileStorage()


async def verify_api_key(x_api_key: Annotated[str | None, Header()] = None) -> str:
    """Verify API Key header.

    Args:
        x_api_key: API Key from X-API-Key header.

    Returns:
        str: Validated API Key.

    Raises:
        HTTPException: 401 if API Key is missing or invalid.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return x_api_key


# Type aliases for dependency injection
SessionDep = Annotated[AsyncSession, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
StorageDep = Annotated[LocalFileStorage, Depends(get_storage)]
ApiKeyDep = Annotated[str, Depends(verify_api_key)]
