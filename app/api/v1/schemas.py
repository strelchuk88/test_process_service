from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import AliasChoices, BaseModel, Field, HttpUrl

from domain.enums.payment import CurrencyEnum, PaymentStatus


class PaymentCreateSchema(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    currency: CurrencyEnum
    description: str = Field(min_length=1, max_length=1000)
    metadata: dict = Field(default_factory=dict)
    webhook_url: HttpUrl

    model_config = {"from_attributes": True}


class PaymentAcceptedSchema(BaseModel):
    payment_id: UUID = Field(validation_alias=AliasChoices("payment_id", "id"))
    status: PaymentStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentReadSchema(BaseModel):
    payment_id: UUID = Field(validation_alias=AliasChoices("payment_id", "id"))
    amount: Decimal
    currency: CurrencyEnum
    description: str
    metadata: dict = Field(validation_alias=AliasChoices("meta", "metadata"))
    status: PaymentStatus
    idempotency_key: str
    webhook_url: str
    created_at: datetime
    processed_at: datetime | None

    model_config = {"from_attributes": True}
