"""Pytest configuration and fixtures."""

from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app
from src.core.config import Settings, get_settings
from src.models.base import Base

# Test database URL (SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session.

    Yields:
        AsyncSession: Test database session.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

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
def override_settings() -> Generator[Settings, None, None]:
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
    original_get_settings = get_settings

    def get_test_settings():
        return test_settings

    # Override dependency
    app.dependency_overrides[get_settings] = get_test_settings
    yield test_settings

    # Restore
    del app.dependency_overrides[get_settings]


@pytest_asyncio.fixture
async def async_client(override_settings: Settings) -> AsyncGenerator[AsyncClient, None]:
    """Provide async HTTP client.

    Args:
        override_settings: Test settings fixture.

    Yields:
        AsyncClient: Async HTTP client.
    """
    async with AsyncClient(
        app=app,
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
