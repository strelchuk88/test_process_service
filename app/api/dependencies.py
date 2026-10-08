from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import Database


def get_db(request: Request) -> Database:
    return request.app.state.db


async def get_session(
    db: Annotated[Database, Depends(get_db)]
) -> AsyncIterator[AsyncSession]:
    async with db.session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
