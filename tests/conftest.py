"""Pytest configuration and fixtures."""

import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app
from src.core.config import Settings, get_settings
from src.models.base import Base

# Test database URL (SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Test engine and session factory to override PostgreSQL in tests
_test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
_TestAsyncSessionLocal = sessionmaker(_test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True, scope="function")
async def _create_test_tables() -> None:
    """Create tables on the test engine for route-level DB access."""
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="session")
def event_loop_policy() -> Any:
    """Provide the asyncio event loop policy for the test session.

    Using event_loop_policy instead of event_loop avoids pytest-asyncio
    deprecation warnings and event loop lifecycle issues across the suite.
    """
    import asyncio

    return asyncio.get_event_loop_policy()


@pytest_asyncio.fixture(scope="function")
async def db_session(
    override_settings: Settings,
) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session.

    Args:
        override_settings: Test settings fixture (ensures AsyncSessionLocal
            resolves to the test database URL).

    Yields:
        AsyncSession: Test database session.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
def override_settings(monkeypatch: pytest.MonkeyPatch) -> Generator[Settings, None, None]:
    """Provide test settings override.

    Yields:
        Settings: Test settings.
    """
    test_settings = Settings(
        database_url=TEST_DATABASE_URL,
        api_key="test-api-key",
        api_rate_limit=100,
        debug=True,
    )

    def get_test_settings() -> Settings:
        return test_settings

    # Clear cached settings so direct calls (e.g. AsyncSessionLocal) pick the test URL
    get_settings.cache_clear()
    # Override the imported get_settings inside infrastructure.database so the
    # dynamic AsyncSessionLocal factory and get_engine use the test database URL.
    monkeypatch.setattr("src.infrastructure.database.get_settings", get_test_settings)
    # Override dependency so FastAPI resolves test settings everywhere
    app.dependency_overrides[get_settings] = get_test_settings
    yield test_settings

    # Restore
    app.dependency_overrides.pop(get_settings, None)
    get_settings.cache_clear()


@pytest_asyncio.fixture(autouse=True)
async def _await_route_background_tasks(
    override_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncGenerator[None, None]:
    """Aguarda tarefas em background iniciadas pela rota de análise.

    Garante que ``asyncio.create_task`` usado em ``analyze_image`` seja
    concluído antes do encerramento do loop de eventos do teste, evitando
    ``RuntimeError: no running event loop`` e acesso a banco fora do escopo.
    """
    background_tasks: list[asyncio.Task] = []
    original_create_task = asyncio.create_task

    def tracked_create_task(coro, *, name=None):  # noqa: ANN001
        task = original_create_task(coro, name=name)
        background_tasks.append(task)
        return task

    monkeypatch.setattr(
        "src.api.routes.threat_model.asyncio.create_task",
        tracked_create_task,
    )
    yield
    if background_tasks:
        await asyncio.gather(*background_tasks, return_exceptions=True)


@pytest_asyncio.fixture
async def async_client(override_settings: Settings) -> AsyncGenerator[AsyncClient, None]:
    """Provide async HTTP client.

    Args:
        override_settings: Test settings fixture.

    Yields:
        AsyncClient: Async HTTP client.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"X-API-Key": "test-api-key"},
    ) as client:
        yield client


@pytest.fixture
def client(override_settings: Settings) -> TestClient:
    """Provide sync HTTP client.

    Args:
        override_settings: Test settings fixture.

    Returns:
        TestClient: Sync HTTP client.
    """
    return TestClient(app, headers={"X-API-Key": "test-api-key"})
