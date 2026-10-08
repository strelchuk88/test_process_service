from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, Enum, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from domain.enums.payment import CurrencyEnum, PaymentStatus
from infrastructure.database.models.base import BaseModel, TimestampMixin


class PaymentModel(TimestampMixin, BaseModel):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint(
            "amount >= 0",
            name="ck_payments_amount_non_negative"
        ),
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    currency: Mapped[CurrencyEnum] = mapped_column(Enum(CurrencyEnum), default=CurrencyEnum.RUB)
    description: Mapped[str] = mapped_column(Text)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True)
    webhook_url: Mapped[str] = mapped_column(String(2048))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
