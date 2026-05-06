from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

_engine: AsyncEngine | None = None
_engine_url: str | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def configure_database(database_url: str | None = None) -> AsyncEngine:
    """Bind the async engine to the configured database URL."""
    global _engine, _engine_url, _sessionmaker

    if database_url:
        settings.DATABASE_URL = database_url

    resolved_url = settings.SQLALCHEMY_DATABASE_URI
    if _engine is not None and _engine_url == resolved_url:
        return _engine

    _engine = create_async_engine(resolved_url, pool_pre_ping=True)
    _engine_url = resolved_url
    _sessionmaker = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    return _engine


def get_engine() -> AsyncEngine:
    if _engine is None:
        return configure_database()
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    if _sessionmaker is None:
        configure_database()
    return _sessionmaker  # type: ignore[return-value]


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting an async database session.
    """
    async with get_sessionmaker()() as session:
        yield session
