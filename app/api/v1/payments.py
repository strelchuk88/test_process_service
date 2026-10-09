from uuid import UUID

from fastapi import APIRouter, Depends, Header, status

from api.dependencies import get_create_payment_use_case, get_payment_service, verify_api_key
from api.v1.schemas import PaymentAcceptedSchema, PaymentCreateSchema, PaymentReadSchema
from application.services.payment import PaymentService
from application.use_cases.create_payment import CreatePaymentUseCase

router = APIRouter(
    prefix="/api/v1/payments",
    tags=["payments"],
    dependencies=[Depends(verify_api_key)]
)


@router.post(
    path="/",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=PaymentAcceptedSchema,
)
async def create_payment(
    data: PaymentCreateSchema,
    uc: CreatePaymentUseCase = Depends(get_create_payment_use_case),
    idempotency_key: str = Header(alias="Idempotency-Key")
) -> PaymentAcceptedSchema:

    payment = await uc.execute(data, idempotency_key)
    return PaymentAcceptedSchema.model_validate(payment)


@router.get(
    path="/{payment_id}",
    response_model=PaymentReadSchema
)
async def get_payment(
    payment_id: UUID,
    service: PaymentService = Depends(get_payment_service),
) -> PaymentReadSchema:

    payment = await service.get(payment_id)
    return PaymentReadSchema.model_validate(payment)
