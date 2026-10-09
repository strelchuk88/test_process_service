import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from domain.enums.payment import PaymentStatus
from domain.exceptions import PaymentNotFoundError
from infrastructure.database.repositories.payment import PaymentRepository
from application.services.gateway import PaymentGateway
from application.services.webhook import WebhookSender

logger = logging.getLogger(__name__)


class ProcessPaymentUseCase:

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        gateway: PaymentGateway,
        webhook: WebhookSender,
    ) -> None:
        self.session_factory = session_factory
        self.gateway = gateway
        self.webhook = webhook

    async def execute(self, payment_id: UUID) -> None:
        async with self.session_factory() as session:
            payment_repository = PaymentRepository(session)

            payment = await payment_repository.get(payment_id)
            if payment is None:
                raise PaymentNotFoundError

            await session.commit()

            if payment.status == PaymentStatus.PENDING:
                succeeded = await self.gateway.charge(payment_id)
                status = PaymentStatus.SUCCEEDED if succeeded else PaymentStatus.FAILED
                if not await payment_repository.finish(payment_id, status):
                    logger.warning("Payment %s was already finished by another delivery", payment_id)
                await session.commit()
                await session.refresh(payment)
                logger.info("Payment %s -> %s", payment_id, payment.status)

        await self.webhook.send(payment)
        logger.info("Webhook for payment %s delivered to %s", payment_id, payment.webhook_url)
