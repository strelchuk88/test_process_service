from uuid import UUID

from pydantic import BaseModel

PAYMENT_CREATED = "payment.created"
ATTEMPT_HEADER = "x-attempt"


class PaymentCreatedMessage(BaseModel):
    payment_id: UUID
