"""Analytics request/response models."""

from __future__ import annotations

from typing import Dict, Optional

from pydantic import BaseModel, Field, validator


class HedgeRatioPayload(BaseModel):
    """Payload describing a hedge ratio computation request."""

    symbol_a: str = Field(..., description="Primary symbol")
    symbol_b: str = Field(..., description="Hedging symbol")
    include_intercept: bool = Field(True, description="Include intercept in regression")

    @validator("symbol_a", "symbol_b")
    def normalize_symbol(cls, value: str) -> str:
        return value.lower()


class AnalyticsRequest(BaseModel):
    """Bundle of analytics parameters for a dashboard refresh."""

    symbol_a: str
    symbol_b: str
    window: int = Field(300, ge=2, description="Rolling window size in observations")
    timeframe: str = Field("1s", description="Resample timeframe string: tick, 1s, 1m, 5m")
    include_intercept: bool = True

    @validator("symbol_a", "symbol_b")
    def normalize_symbols(cls, value: str) -> str:
        return value.lower()

    @validator("timeframe")
    def validate_timeframe(cls, value: str) -> str:
        valid = {"tick", "1s", "1m", "5m"}
        if value.lower() not in valid:
            raise ValueError(f"timeframe must be one of {sorted(valid)}")
        return value.lower()


class HedgeRatioResponse(BaseModel):
    beta: float
    intercept: Optional[float]
    rvalue: Optional[float]
    pvalue: Optional[float]
    stderr: Optional[float]


class ADFPayload(BaseModel):
    statistic: float
    pvalue: float
    lags: int
    nobs: int
    critical_values: Dict[str, float]


class AnalyticsResponse(BaseModel):
    hedge_ratio: HedgeRatioResponse
    latest_spread: Optional[float]
    latest_zscore: Optional[float]
    rolling_correlation: Optional[float]
    adf: Optional[ADFPayload]



