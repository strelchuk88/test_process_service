from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.database import Database
from core.settings import settings
from infrastructure.broker.broker import Broker
from infrastructure.broker.topology import declare


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = Database(settings.db)
    broker = Broker(settings.rabbit)
    await broker.start()
    topology = await declare(broker.rabbit, settings.rabbit)

    app.state.db = db
    app.state.broker = broker
    app.state.topology = topology
    try:
        yield
    finally:
        await broker.stop()
        await db.dispose()
