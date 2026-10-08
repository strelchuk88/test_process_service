class AppError(Exception):
    status_code = 400
    message = 'Bad Request'

    def __init__(self, message: str | None = None):
        self.message = message or self.message
        super().__init__(self.message)


class IdempotencyConflictError(AppError):
    status_code = 409
    message = "Idempotency-Key has already been used"


class InvalidAPIKey(AppError):
    status_code = 401
    message = "Invalid or missing API key"


class PaymentNotFoundError(AppError):
    status_code = 404
    message = "Payment not found"
