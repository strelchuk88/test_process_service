from typing import AsyncIterator

from fastapi import Depends, Request, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import Database
from domain.exceptions import InvalidAPIKey
from infrastructure.broker.broker import Broker
from application.services.payment import PaymentService
from application.use_cases.create_payment import CreatePaymentUseCase

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_db(request: Request) -> Database:
    return request.app.state.db


def get_broker(request: Request) -> Broker:
    return request.app.state.broker


async def get_session(db = Depends(get_db)) -> AsyncIterator[AsyncSession]:
    async with db.session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


def get_payment_service(
    session: AsyncSession = Depends(get_session)
) -> PaymentService:
    return PaymentService(session)


def get_create_payment_use_case(
    session: AsyncSession = Depends(get_session)
) -> CreatePaymentUseCase:
    return CreatePaymentUseCase(session)


async def verify_api_key(api_key: str = Security(api_key_header)) -> None:
    if api_key is None:
        raise InvalidAPIKey
