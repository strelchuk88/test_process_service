from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.database import Database
from core.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = Database(settings.db)
    app.state.db = db
    yield
    await db.dispose()
