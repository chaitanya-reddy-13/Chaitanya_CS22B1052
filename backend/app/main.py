"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.routers import api_router
from backend.core.config import settings
from backend.services import (
    ingest_service,
    live_metrics_stream,
    persistence_worker,
)
from backend.storage import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):  # pragma: no cover - integration setup
    init_db()
    ingest_service.add_subscriber(persistence_worker.queue)
    await ingest_service.start()
    await persistence_worker.start()
    await live_metrics_stream.start()
    try:
        yield
    finally:
        await live_metrics_stream.stop()
        await persistence_worker.stop()
        await ingest_service.stop()
        ingest_service.remove_subscriber(persistence_worker.queue)


def create_app() -> FastAPI:
    """Instantiate and configure the FastAPI application."""

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Backend services for the Binance analytics project.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api")

    @app.get("/", tags=["health"])
    async def root() -> dict[str, str]:
        return {"status": "ok", "service": settings.app_name}

    return app


app = create_app()



