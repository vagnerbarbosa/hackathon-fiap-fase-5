"""Provedores de injeção de dependência do FastAPI."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings, get_settings
from src.core.logging import get_logger
from src.infrastructure.database import get_async_session_maker
from src.infrastructure.storage import LocalFileStorage

logger = get_logger(__name__)


async def get_db(
    settings: Settings = Depends(get_settings),
) -> AsyncGenerator[AsyncSession, None]:
    """Fornece dependência de sessão do banco de dados.

    Usa settings.database_url para permitir override em testes via
    app.dependency_overrides[get_settings].

    Yields:
        AsyncSession: Sessão do banco de dados.
    """
    session_factory = get_async_session_maker(settings.database_url)
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_storage() -> LocalFileStorage:
    """Fornece dependência de armazenamento de arquivos.

    Returns:
        LocalFileStorage: Instância do serviço de armazenamento.
    """
    return LocalFileStorage()


async def verify_api_key(
    x_api_key: Annotated[str | None, Header()] = None,
    settings: Settings = Depends(get_settings),
) -> str:
    """Verifica header de API Key.

    Args:
        x_api_key: API Key do header X-API-Key.
        settings: Configurações da aplicação (injetadas).

    Returns:
        str: API Key validada.

    Raises:
        HTTPException: 401 se a API Key estiver ausente ou inválida.
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
