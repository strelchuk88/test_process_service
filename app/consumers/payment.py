import logging

from faststream import AckPolicy, Context
from faststream.rabbit import ExchangeType, RabbitExchange, RabbitQueue, RabbitRouter
from faststream.rabbit.annotations import RabbitBroker, RabbitMessage

from application.payment.use_cases.process_payment import ProcessPaymentUseCase
from core.settings import settings
from domain.exceptions import PaymentNotFoundError
from infrastructure.broker import config
from infrastructure.broker.messages import ATTEMPT_HEADER, PaymentCreatedMessage
from infrastructure.broker.retry import publish_retry

logger = logging.getLogger(__name__)

router = RabbitRouter()

payments_exchange = RabbitExchange(config.PAYMENTS_EXCHANGE, type=ExchangeType.TOPIC, declare=False)
payments_queue = RabbitQueue(config.PAYMENTS_QUEUE, routing_key=config.PAYMENTS_QUEUE, declare=False)


@router.subscriber(payments_queue, payments_exchange, ack_policy=AckPolicy.REJECT_ON_ERROR)
async def handle_payment_created(
    message: PaymentCreatedMessage,
    raw: RabbitMessage,
    broker: RabbitBroker,
    use_case: ProcessPaymentUseCase = Context("process_payment_use_case"),
) -> None:
    attempt = int(raw.headers.get(ATTEMPT_HEADER, 1))
    logger.info(
        "Processing payment %s (attempt %d/%d)",
        message.payment_id, attempt, settings.rabbit.max_attempts
    )

    try:
        await use_case.execute(message.payment_id)
    except PaymentNotFoundError:
        logger.error("Payment %s not found, sending to DLQ", message.payment_id)
        raise
    except Exception as error:
        if attempt >= settings.rabbit.max_attempts:
            logger.exception(
                "Payment %s failed after %d attempts, sending to DLQ",
                message.payment_id, attempt
            )
            raise

        try:
            retry_queue = await publish_retry(broker, message, attempt, raw.message_id)
        except Exception:
            logger.exception("Failed to schedule retry for payment %s, requeueing", message.payment_id)
            await raw.nack(requeue=True)
            return

        logger.warning(
            "Attempt %d for payment %s failed: %r. Retrying via %s",
            attempt, message.payment_id, error, retry_queue
        )
