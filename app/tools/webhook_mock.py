import logging
from typing import Any

from fastapi import FastAPI, Request, Response

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [webhook-mock] %(message)s")
logger = logging.getLogger("webhook-mock")

app = FastAPI(title="Webhook mock")
received: list[dict[str, Any]] = []


@app.post("/webhook")
async def webhook(request: Request) -> dict[str, str]:
    body = await request.json()
    received.append(body)
    logger.info("Received: %s", body)
    return {"status": "ok"}


@app.post("/fail")
async def fail(request: Request) -> Response:
    body = await request.json()
    logger.info("Rejecting webhook for payment %s", body.get("payment_id"))
    return Response(status_code=500)


@app.get("/received")
async def get_received() -> list[dict[str, Any]]:
    return received
