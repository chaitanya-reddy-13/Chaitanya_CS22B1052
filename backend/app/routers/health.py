"""Healthcheck endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter()


@router.get("/", summary="Service healthcheck")
async def health_check() -> dict[str, str]:
    """Return a simple uptime heartbeat."""

    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }



