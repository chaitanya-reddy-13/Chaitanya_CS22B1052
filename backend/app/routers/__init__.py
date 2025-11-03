"""API router registry."""

from fastapi import APIRouter

from . import alerts, analytics, data, health, live

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(data.router, prefix="/data", tags=["data"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(live.router, prefix="/ws", tags=["live"])


