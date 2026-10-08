from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from domain.enums.payment import PaymentStatus
from infrastructure.database.models.payment import PaymentModel


class PaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add(self, payment: PaymentModel) -> None:
        self.session.add(payment)

    async def get(self, payment_id: UUID) -> PaymentModel | None:
        result = await self.session.execute(
            select(PaymentModel)
            .where(PaymentModel.id == payment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_idempotency_key(self, key: str) -> PaymentModel | None:
        result = await self.session.execute(
            select(PaymentModel)
            .where(PaymentModel.idempotency_key == key)
        )
        return result.scalar_one_or_none()

    async def finish(self, payment_id: UUID, status: PaymentStatus) -> bool:
        result = await self.session.execute(
            update(PaymentModel)
            .where(PaymentModel.id == payment_id, PaymentModel.status == PaymentStatus.PENDING)
            .values(status=status, processed_at=datetime.now(UTC))
            .returning(PaymentModel.id)
        )
        return result.scalar_one_or_none() is not None
