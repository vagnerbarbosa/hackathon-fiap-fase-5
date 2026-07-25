"""Configuração do banco de dados com SQLAlchemy async."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)

# Engine cache keyed by database URL so tests can switch URLs safely.
_engines: dict[str, AsyncEngine] = {}


def get_engine(database_url: str | None = None) -> AsyncEngine:
    """Obtém ou cria engine async baseado na URL fornecida ou nas configurações.

    O engine é cacheado por URL para evitar recriação a cada requisição.

    Args:
        database_url: URL do banco de dados. Se None, usa get_settings().database_url.

    Returns:
        AsyncEngine: Engine async configurado.
    """
    url = database_url or get_settings().database_url
    if url not in _engines:
        settings = get_settings()
        is_sqlite = url.startswith("sqlite")
        pool_kwargs = (
            {}
            if is_sqlite
            else {
                "pool_size": 5,
                "max_overflow": 10,
                "pool_pre_ping": True,
                "pool_recycle": 3600,
            }
        )
        _engines[url] = create_async_engine(
            url,
            echo=settings.debug,
            **pool_kwargs,
        )
    return _engines[url]


def get_async_session_maker(
    database_url: str | None = None,
) -> async_sessionmaker[AsyncSession]:
    """Obtém factory de sessões baseada no engine atual.

    Args:
        database_url: URL do banco de dados. Se None, usa get_settings().database_url.

    Returns:
        async_sessionmaker: Factory de sessões async.
    """
    return async_sessionmaker(
        get_engine(database_url),
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


class _DynamicAsyncSessionLocal:
    """Factory dinâmica de sessões que respeita get_settings() em runtime.

    Garante que testes com override de get_settings usem o engine correto,
    mesmo quando AsyncSessionLocal é importado em tempo de importação.
    """

    def __call__(self) -> AsyncSession:
        return get_async_session_maker()()


# Backwards-compatible alias used by legacy code/tests.
AsyncSessionLocal = _DynamicAsyncSessionLocal()


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Obtém sessão do banco de dados como gerenciador de contexto async.

    Yields:
        AsyncSession: Sessão do banco de dados.

    Exemplo:
        async with get_session() as session:
            result = await session.execute(query)
    """
    session_factory = get_async_session_maker()
    session = session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Fornece dependência de sessão do banco de dados para FastAPI.

    Yields:
        AsyncSession: Sessão do banco de dados.
    """
    session_factory = get_async_session_maker()
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def close_engine() -> None:
    """Fecha conexões de todos os engines criados."""
    for engine in _engines.values():
        await engine.dispose()
    _engines.clear()
    logger.info("Database engines disposed")


async def test_connection() -> bool:
    """Testa conectividade do banco de dados.

    Returns:
        bool: True se a conexão for bem-sucedida, False caso contrário.
    """
    try:
        async with get_engine().connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False
