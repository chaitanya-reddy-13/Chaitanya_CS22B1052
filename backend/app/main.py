"""FastAPI application entrypoint."""

import asyncio
import logging
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
    
    # Start services in background without blocking - allow REST API to start even if WebSocket fails
    # Use asyncio.create_task to start services in background without waiting
    async def start_services_async():
        try:
            await ingest_service.start()
        except Exception as exc:
            logging.warning("Ingest service startup failed: %s, continuing anyway...", exc)
        
        try:
            await persistence_worker.start()
        except Exception as exc:
            logging.warning("Persistence worker startup failed: %s, continuing anyway...", exc)
        
        try:
            await live_metrics_stream.start()
        except Exception as exc:
            logging.warning("Live metrics stream startup failed: %s, continuing anyway...", exc)
    
    # Start services in background - don't wait for them
    asyncio.create_task(start_services_async())
    
    try:
        yield
    finally:
        try:
            await live_metrics_stream.stop()
        except Exception:
            pass
        try:
            await persistence_worker.stop()
        except Exception:
            pass
        try:
            await ingest_service.stop()
        except Exception:
            pass
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



