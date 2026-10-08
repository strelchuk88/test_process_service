import logging

from fastapi import FastAPI

from api.exception_handlers import register_exception_handlers
from api.v1.payments import router as api_v1_router
from core.lifespan import lifespan


def create_app():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")

    app = FastAPI(
        debug=True,
        docs_url="/api/docs",
        title="Process Service",
        lifespan=lifespan
    )
    app.include_router(api_v1_router)
    register_exception_handlers(app)
    return app
