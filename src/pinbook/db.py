"""Async SQLAlchemy plumbing."""
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def build_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(database_url)


def build_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    # expire_on_commit=False keeps loaded attributes readable after commit,
    # which matters in async code where lazy refresh is not possible.
    return async_sessionmaker(engine, expire_on_commit=False)
