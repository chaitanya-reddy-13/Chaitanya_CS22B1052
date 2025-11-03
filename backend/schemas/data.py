"""Data-related response models."""

from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class OHLCBar(BaseModel):
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class HistoryResponse(BaseModel):
    symbol: str = Field(..., description="Symbol in lowercase")
    timeframe: str
    bars: List[OHLCBar]


