"""Async SQLAlchemy engine + session factory.

A single engine is constructed at import time using the DSN from settings.
FastAPI handlers should depend on `get_session()` so each request gets its
own session that is closed (and rolled back on error) automatically.
"""
from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=False,
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: yields an AsyncSession scoped to a single request."""
    async with SessionLocal() as session:
        yield session
