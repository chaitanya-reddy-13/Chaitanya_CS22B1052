"""Tick-related request and response models."""

from datetime import datetime

from pydantic import BaseModel, Field


class Tick(BaseModel):
    """Normalized representation of a trade tick."""

    symbol: str = Field(..., description="Trading symbol, e.g. btcusdt")
    ts: datetime = Field(..., description="Event timestamp in UTC")
    price: float = Field(..., ge=0, description="Trade price")
    size: float = Field(..., ge=0, description="Trade size or volume")



