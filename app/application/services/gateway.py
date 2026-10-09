import asyncio
import logging
import random
from uuid import UUID

from core.settings import GatewaySettings

logger = logging.getLogger(__name__)


class PaymentGateway:
    """Emulation of an external payment gateway: random latency and success rate."""

    def __init__(self, settings: GatewaySettings) -> None:
        self.settings = settings

    async def charge(self, payment_id: UUID) -> bool:
        await asyncio.sleep(random.uniform(self.settings.min_delay, self.settings.max_delay))
        succeeded = random.random() < self.settings.success_rate
        logger.info("Gateway %s payment %s", "accepted" if succeeded else "declined", payment_id)
        return succeeded
