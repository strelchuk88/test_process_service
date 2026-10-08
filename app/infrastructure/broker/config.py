# Exchanges
PAYMENTS_EXCHANGE = "payments"
DLX = "payments.dlx"

# Queues
PAYMENTS_QUEUE = "payment.create"
DLQ = "payment.dlq"
PAYMENTS_RETRY_QUEUE_TEMPLATE = f"{PAYMENTS_QUEUE}.retry.{{attempt}}"
