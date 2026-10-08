from faststream.rabbit import RabbitBroker

from infrastructure.broker import config
from infrastructure.broker.messages import ATTEMPT_HEADER, PaymentCreatedMessage


async def publish_retry(
    broker: RabbitBroker,
    message: PaymentCreatedMessage,
    attempt: int,
    message_id: str | None = None,
) -> str:

    retry_queue = config.PAYMENTS_RETRY_QUEUE_TEMPLATE.format(attempt=attempt)
    await broker.publish(
        message,
        queue=retry_queue,
        message_id=message_id,
        headers={ATTEMPT_HEADER: attempt + 1},
        persist=True
    )
    return retry_queue
