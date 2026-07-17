import asyncio
import os
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient, ASGITransport

# Set default test environment parameters
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from app.main import app as fastapi_app
from app.db.session import get_db
from app.db.base_class import Base

# Import all models to register them on Base.metadata
import app.db.base  # noqa

# 1. Initialize Async Engine targeting the Test Database
test_engine = create_async_engine(
    os.environ["DATABASE_URL"],
    echo=False
)

TestSessionLocal = sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Creates an instance of the default event loop for the session scope.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_database() -> AsyncGenerator[None, None]:
    """
    Bootstraps the test database on startup: creates tables, and drops them on teardown.
    """
    async with test_engine.begin() as conn:
        # Drop existing tables to ensure a clean sandbox run
        await conn.run_sync(Base.metadata.drop_all)
        # Create all registered tables
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    async with test_engine.begin() as conn:
        # Tear down tables on completion
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields an isolated test database session. Automatically rolls back all writes
    and overrides close to support multi-request integration tests.
    """
    async with TestSessionLocal() as session:
        # Mock close to prevent FastAPI dependency injectors from closing the session between requests
        async def mock_close():
            pass
        session.close = mock_close
        
        yield session
        
        # Rollback all operations to restore database sandbox state
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Returns an async HTTP client configured with dependency overrides for get_db.
    """
    # Override FastAPI DB connection dependency to use our isolated test transaction
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = _override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://testserver"
    ) as async_client:
        yield async_client

    # Clean overrides
    fastapi_app.dependency_overrides.clear()
