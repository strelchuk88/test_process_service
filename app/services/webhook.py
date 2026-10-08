from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

import httpx
from pydantic import BaseModel

from domain.enums.payment import CurrencyEnum, PaymentStatus
from infrastructure.database.models.payment import PaymentModel


class PaymentWebhook(BaseModel):
    event: str
    payment_id: UUID
    status: PaymentStatus
    amount: Decimal
    currency: CurrencyEnum
    description: str
    metadata: dict[str, Any]
    created_at: datetime
    processed_at: datetime | None


class WebhookSender:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client

    async def send(self, payment: PaymentModel) -> None:
        body = PaymentWebhook(
            event=f"payment.{payment.status.value}",
            payment_id=payment.id,
            status=payment.status,
            amount=payment.amount,
            currency=payment.currency,
            description=payment.description,
            metadata=payment.meta,
            created_at=payment.created_at,
            processed_at=payment.processed_at
        )
        response = await self.client.post(
            payment.webhook_url,
            content=body.model_dump_json(),
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
