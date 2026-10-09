from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.schemas import PaymentCreateSchema
from domain.exceptions import IdempotencyConflictError
from infrastructure.broker import config
from infrastructure.broker.messages import PAYMENT_CREATED, PaymentCreatedMessage
from infrastructure.database.models.payment import PaymentModel
from infrastructure.database.repositories.outbox import OutboxRepository
from infrastructure.database.repositories.payment import PaymentRepository


class CreatePaymentUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.payment_repository = PaymentRepository(session)
        self.outbox_repository = OutboxRepository(session)

    async def execute(self, data: PaymentCreateSchema, idempotency_key: str) -> PaymentModel:

        existing = await self.payment_repository.get_by_idempotency_key(idempotency_key)
        if existing is not None:
            return existing

        payment = PaymentModel(
            id=uuid4(),
            amount=data.amount,
            currency=data.currency,
            description=data.description,
            meta=data.metadata,
            idempotency_key=idempotency_key,
            webhook_url=str(data.webhook_url)
        )
        self.payment_repository.add(payment)
        self.outbox_repository.add(
            event_type=PAYMENT_CREATED,
            routing_key=config.PAYMENTS_QUEUE,
            payload=PaymentCreatedMessage(payment_id=payment.id).model_dump(mode="json")
        )

        try:
            await self.session.commit()
            await self.session.refresh(payment)
            return payment
        except IntegrityError:
            await self.session.rollback()
            raise IdempotencyConflictError
