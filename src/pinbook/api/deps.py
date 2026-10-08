"""FastAPI dependencies."""
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from pinbook.repository import ContactRepository
from pinbook.settings import Settings


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.sessionmaker() as session:
        yield session


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_repository(session: Annotated[AsyncSession, Depends(get_session)]) -> ContactRepository:
    return ContactRepository(session)


Repository = Annotated[ContactRepository, Depends(get_repository)]
AppSettings = Annotated[Settings, Depends(get_settings)]
