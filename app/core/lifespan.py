import asyncio
import contextlib
from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.database import Database
from core.settings import settings
from infrastructure.broker.broker import Broker
from infrastructure.broker.topology import declare
from infrastructure.outbox.relay import OutboxRelay


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = Database(settings.db)
    broker = Broker(settings.rabbit)
    await broker.start()
    topology = await declare(broker.rabbit, settings.rabbit)

    relay = OutboxRelay(broker.rabbit, db.session_factory, settings.outbox)
    relay_task = asyncio.create_task(relay.run(), name="outbox-relay")

    app.state.db = db
    app.state.broker = broker
    app.state.topology = topology
    try:
        yield
    finally:
        relay_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await relay_task
        await broker.stop()
        await db.dispose()
