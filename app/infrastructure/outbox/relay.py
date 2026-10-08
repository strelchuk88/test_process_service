import asyncio
import logging

from faststream.rabbit import RabbitBroker
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.settings import OutboxSettings
from infrastructure.broker import config
from infrastructure.database.repositories.outbox import OutboxRepository

logger = logging.getLogger(__name__)


class OutboxRelay:

    def __init__(
        self,
        broker: RabbitBroker,
        session_factory: async_sessionmaker[AsyncSession],
        settings: OutboxSettings,
    ) -> None:
        self.broker = broker
        self.session_factory = session_factory
        self.settings = settings

    async def run(self) -> None:
        logger.info("Outbox relay started")
        while True:
            try:
                published = await self.publish_batch()
            except Exception:
                logger.exception("Outbox relay iteration failed")
                published = 0

            if published < self.settings.batch_size:
                await asyncio.sleep(self.settings.poll_interval)

    async def publish_batch(self) -> int:
        published = 0
        async with self.session_factory() as session, session.begin():
            repository = OutboxRepository(session)
            for event in await repository.lock_unpublished(self.settings.batch_size):
                try:
                    await self.broker.publish(
                        event.payload,
                        exchange=config.PAYMENTS_EXCHANGE,
                        routing_key=event.routing_key,
                        message_id=str(event.id),
                        message_type=event.event_type,
                        persist=True
                    )
                except Exception as error:
                    repository.mark_failed(event, error)
                    logger.warning("Failed to publish outbox event %s: %r", event.id, error)
                    break
                repository.mark_published(event)
                published += 1

        if published:
            logger.info("Published %d outbox event(s)", published)
        return published
