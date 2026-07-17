from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

# For async operations, we must use the asyncpg driver dialect.
# If the connection string does not specify +asyncpg, we inject it automatically.
database_url = settings.DATABASE_URL
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Create the async engine with our connection pool configurations
if database_url.startswith("sqlite"):
    engine = create_async_engine(
        database_url,
        echo=settings.ENVIRONMENT == "development", # Log SQL queries in dev mode
    )
else:
    engine = create_async_engine(
        database_url,
        pool_size=settings.POSTGRES_POOL_SIZE,
        max_overflow=settings.POSTGRES_MAX_OVERFLOW,
        pool_recycle=settings.POSTGRES_POOL_RECYCLE,
        pool_timeout=settings.POSTGRES_POOL_TIMEOUT,
        echo=settings.ENVIRONMENT == "development", # Log SQL queries in dev mode
    )

# Create the async session factory
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False, # Prevents attributes from expiring after commit
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency injection helper that yields an async database session.
    Automatically handles transaction boundaries, rolling back on exception,
    and closing the connection when the request completes.
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
