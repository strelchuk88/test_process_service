from dataclasses import dataclass

from faststream.rabbit import ExchangeType, RabbitBroker, RabbitExchange, RabbitQueue

from core.settings import RabbitSettings
from infrastructure.broker import config


@dataclass(frozen=True)
class Topology:
    exchange: RabbitExchange
    queue: RabbitQueue


async def declare(broker: RabbitBroker, rabbit_settings: RabbitSettings) -> Topology:
    exchange = await broker.declare_exchange(
        RabbitExchange(
            config.PAYMENTS_EXCHANGE,
            type=ExchangeType.TOPIC,
            durable=True
        )
    )

    dlx = await broker.declare_exchange(
        RabbitExchange(
            config.DLX,
            type=ExchangeType.FANOUT,
            durable=True
        )
    )

    # noinspection PyTypeChecker
    queue = await broker.declare_queue(
        RabbitQueue(
            config.PAYMENTS_QUEUE,
            durable=True,
            arguments={
                "x-dead-letter-exchange": config.DLX,
            }
        )
    )
    await queue.bind(exchange, routing_key=config.PAYMENTS_QUEUE)

    dlq = await broker.declare_queue(
        RabbitQueue(
            config.DLQ,
            durable=True
        )
    )
    await dlq.bind(dlx)

    for attempt in range(1, rabbit_settings.max_attempts):
        retry_queue_name = config.PAYMENTS_RETRY_QUEUE_TEMPLATE.format(attempt=attempt)
        delay = rabbit_settings.retry_base_delay * 2 ** (attempt - 1)

        await broker.declare_queue(
            RabbitQueue(
                retry_queue_name,
                durable=True,
                arguments={
                    "x-message-ttl": int(delay * 1000),
                    "x-dead-letter-exchange": config.PAYMENTS_EXCHANGE,
                    "x-dead-letter-routing-key": config.PAYMENTS_QUEUE
                }
            )
        )

    return Topology(exchange=exchange, queue=queue)
