from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine

from app.db.models import Base  # noqa: F401 - importing registers all models
from app.db.session import get_engine


async def create_schema(engine: AsyncEngine | None = None) -> None:
    """Create all database tables for the configured metadata."""
    active_engine = engine or get_engine()
    async with active_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def drop_schema(engine: AsyncEngine | None = None) -> None:
    """Drop all database tables for cleanup in tests."""
    active_engine = engine or get_engine()
    async with active_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
