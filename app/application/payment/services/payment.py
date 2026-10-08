from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from domain.exceptions import PaymentNotFoundError
from infrastructure.database.models.payment import PaymentModel
from infrastructure.database.repositories.payment import PaymentRepository


class PaymentService:
    def __init__(self, session: AsyncSession) -> None:
        self.payments = PaymentRepository(session)

    async def get(self, payment_id: UUID) -> PaymentModel | None:
        payment = await self.payments.get(payment_id)
        if payment is None:
            raise PaymentNotFoundError

        return payment
