from fastapi import FastAPI

from app.api.routes import api_router
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Production-style AI copilot for engineering and operations workflows.",
    )
    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
