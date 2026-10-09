from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.models.outbox import OutboxModel


class OutboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add(self, event_type: str, routing_key: str, payload: dict) -> None:
        self.session.add(
            OutboxModel(
                event_type=event_type,
                routing_key=routing_key,
                payload=payload
            )
        )

    async def lock_unpublished(self, limit: int) -> Sequence[OutboxModel]:
        result = await self.session.execute(
            select(OutboxModel)
            .where(OutboxModel.published_at.is_(None))
            .order_by(OutboxModel.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return result.scalars().all()

    @staticmethod
    def mark_published(event: OutboxModel) -> None:
        event.published_at = datetime.now(UTC)
        event.attempts += 1

    @staticmethod
    def mark_failed(event: OutboxModel, error: Exception) -> None:
        event.attempts += 1
        event.last_error = repr(error)
