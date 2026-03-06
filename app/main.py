from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.api.routes import api_router
from app.core.config import settings
from app.core.storage import storage
from app.graphql.schema import graphql_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    storage.initialize()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Production-style AI copilot for engineering and operations workflows.",
        lifespan=lifespan,
    )

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def demo_page() -> str:
        return Path("app/web/demo.html").read_text(encoding="utf-8")

    app.include_router(api_router, prefix=settings.api_prefix)
    app.include_router(graphql_router, prefix=settings.graphql_path, include_in_schema=False)
    return app


app = create_app()
