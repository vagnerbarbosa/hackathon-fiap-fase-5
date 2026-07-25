"""Tests for src.infrastructure.database helpers."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from src.infrastructure.database import (
    AsyncSessionLocal,
    _engines,
    close_engine,
    get_async_session_maker,
    get_engine,
    get_session,
    test_connection,
)


@pytest.mark.asyncio
async def test_get_engine_caches_by_url() -> None:
    """Engines should be cached per database URL."""
    engine1 = get_engine("sqlite+aiosqlite:///:memory:")
    engine2 = get_engine("sqlite+aiosqlite:///:memory:")

    assert isinstance(engine1, AsyncEngine)
    assert engine1 is engine2

    await close_engine()


@pytest.mark.asyncio
async def test_get_async_session_maker_uses_provided_url() -> None:
    """Session maker should use the provided database URL."""
    session_maker = get_async_session_maker("sqlite+aiosqlite:///:memory:")
    async with session_maker() as session:
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1

    await close_engine()


@pytest.mark.asyncio
async def test_get_session_commits_on_success() -> None:
    """get_session should commit when no exception is raised."""
    async with get_session() as session:
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1

    await close_engine()


@pytest.mark.asyncio
async def test_get_session_rolls_back_on_error() -> None:
    """get_session should roll back when an exception occurs."""
    with pytest.raises(RuntimeError):
        async with get_session():
            raise RuntimeError("boom")

    await close_engine()


@pytest.mark.asyncio
async def test_async_session_local_returns_usable_session() -> None:
    """AsyncSessionLocal should return a working async session."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1

    await close_engine()


@pytest.mark.asyncio
async def test_test_connection_succeeds_for_sqlite() -> None:
    """test_connection should return True for a valid SQLite URL."""
    get_engine("sqlite+aiosqlite:///:memory:")

    assert await test_connection() is True

    await close_engine()


@pytest.mark.asyncio
async def test_close_engine_clears_cache() -> None:
    """close_engine should dispose engines and clear the cache."""
    get_engine("sqlite+aiosqlite:///:memory:")
    assert _engines

    await close_engine()
    assert not _engines
