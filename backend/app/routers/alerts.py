"""Alert management API endpoints."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Path

from backend.schemas import (
    Alert,
    AlertCreate,
    AlertHistoryResponse,
    AlertListResponse,
)
from backend.services import alert_manager

router = APIRouter()


@router.get("/", response_model=AlertListResponse)
async def list_alerts() -> AlertListResponse:
    return AlertListResponse(alerts=alert_manager.list_alerts())


@router.post("/", response_model=Alert)
async def create_alert(payload: AlertCreate) -> Alert:
    return alert_manager.create_alert(payload)


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(alert_id: UUID = Path(...)) -> None:
    try:
        alert_manager.delete_alert(alert_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Alert not found") from exc


@router.post("/{alert_id}/toggle", response_model=Alert)
async def toggle_alert(
    alert_id: UUID = Path(...), *, active: Optional[bool] = None
) -> Alert:
    if active is None:
        raise HTTPException(status_code=400, detail="Provide 'active' query parameter")
    try:
        return alert_manager.toggle_alert(alert_id, active)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Alert not found") from exc


@router.get("/history", response_model=AlertHistoryResponse)
async def alert_history() -> AlertHistoryResponse:
    return AlertHistoryResponse(events=alert_manager.history())


