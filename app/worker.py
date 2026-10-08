import logging

import httpx
from faststream import ContextRepo, FastStream
from faststream.rabbit import RabbitBroker

from application.payment.use_cases.process_payment import ProcessPaymentUseCase
from consumers.payment import router as payment_router
from core.database import Database
from core.settings import settings
from infrastructure.broker.topology import declare
from services.gateway import PaymentGateway
from services.webhook import WebhookSender

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")

broker = RabbitBroker(str(settings.rabbit.url))
broker.include_router(payment_router)

app = FastStream(broker)

db = Database(settings.db)
http_client = httpx.AsyncClient(timeout=settings.webhook.timeout)


@app.on_startup
async def startup(context: ContextRepo) -> None:
    await broker.connect()
    await declare(broker, settings.rabbit)

    context.set_global(
        "process_payment_use_case",
        ProcessPaymentUseCase(
            db.session_factory,
            PaymentGateway(settings.gateway),
            WebhookSender(http_client)
        )
    )


@app.after_shutdown
async def shutdown() -> None:
    await http_client.aclose()
    await db.dispose()
