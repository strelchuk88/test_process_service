from fastapi import FastAPI

from core.lifespan import lifespan


def create_app():
    app = FastAPI(
        debug=True,
        docs_url="/api/docs",
        title="Process Service",
        lifespan=lifespan
    )
    return app
