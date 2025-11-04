"""Analytics endpoints exposing quantitative computations."""

from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, HTTPException, Query

from backend.core.config import settings
from backend.schemas import (
    ADFPayload,
    AnalyticsRequest,
    AnalyticsResponse,
    HedgeRatioPayload,
    HedgeRatioResponse,
)
from backend.services import compute_pair_metrics, ingest_service
from backend.storage import fetch_recent_ticks

router = APIRouter()


TIMEFRAME_MAP = {
    "tick": None,
    "1s": "1s",
    "1m": "1Min",
    "5m": "5Min",
}


def _resolve_timeframe(timeframe: str | None) -> str | None:
    if timeframe is None:
        return None
    tf = TIMEFRAME_MAP.get(timeframe.lower())
    if timeframe.lower() not in TIMEFRAME_MAP:
        raise HTTPException(status_code=400, detail=f"Unsupported timeframe '{timeframe}'")
    return tf


def _merge_ticks(symbol: str, limit: int) -> List:
    db_ticks = fetch_recent_ticks(symbol, limit)
    buffer_ticks = ingest_service.buffer.snapshot(symbol)
    seen: Dict[str, object] = {}
    for tick in db_ticks + buffer_ticks:
        seen[tick.ts.isoformat()] = tick
    merged = sorted(seen.values(), key=lambda t: t.ts)
    if len(merged) > limit:
        merged = merged[-limit:]
    return merged


async def _prepare_ticks(symbol: str, window: int, timeframe: str) -> List:
    await ingest_service.add_symbol(symbol)
    limit = max(window * 5, 2000)
    ticks = _merge_ticks(symbol, limit)
    if not ticks:
        raise HTTPException(status_code=404, detail=f"No data available for {symbol}")

    resolved = _resolve_timeframe(timeframe)
    if resolved is None:
        return ticks

    from backend.services.metrics import resample_ticks as resample_helper
    from backend.schemas.tick import Tick
    from datetime import timezone

    df = resample_helper(ticks, resolved).dropna()

    resampled: List[Tick] = []
    for ts, row in df.iterrows():
        resampled.append(
            Tick(
                symbol=symbol,
                ts=ts.to_pydatetime().astimezone(timezone.utc),
                price=float(row["close"]),
                size=float(row.get("volume", 0.0) or 0.0),
            )
        )
    return resampled or ticks


async def _compute(request: AnalyticsRequest, include_adf: bool) -> AnalyticsResponse:
    from backend.schemas import HedgeRatioResponse
    
    try:
        ticks_a = await _prepare_ticks(request.symbol_a, request.window, request.timeframe)
        ticks_b = await _prepare_ticks(request.symbol_b, request.window, request.timeframe)
    except HTTPException as exc:
        # If no data available, return empty analytics instead of 404
        if exc.status_code == 404:
            return AnalyticsResponse(
                hedge_ratio=HedgeRatioResponse(
                    beta=0.0, intercept=0.0, rvalue=None, pvalue=None, stderr=None
                ),
                latest_spread=None,
                latest_zscore=None,
                rolling_correlation=None,
                adf=None,
            )
        raise
    except Exception as exc:
        # Return empty analytics on any other error
        return AnalyticsResponse(
            hedge_ratio=HedgeRatioResponse(
                beta=0.0, intercept=0.0, rvalue=None, pvalue=None, stderr=None
            ),
            latest_spread=None,
            latest_zscore=None,
            rolling_correlation=None,
            adf=None,
        )
    
    try:
        analytics, _ = compute_pair_metrics(
            ticks_a,
            ticks_b,
            window=request.window,
            include_intercept=request.include_intercept,
            adf=include_adf,
        )
        return analytics
    except Exception:
        # Return empty analytics if computation fails (e.g., insufficient data)
        return AnalyticsResponse(
            hedge_ratio=HedgeRatioResponse(
                beta=0.0, intercept=0.0, rvalue=None, pvalue=None, stderr=None
            ),
            latest_spread=None,
            latest_zscore=None,
            rolling_correlation=None,
            adf=None,
        )


@router.post("/hedge-ratio", response_model=HedgeRatioResponse)
async def hedge_ratio(payload: HedgeRatioPayload) -> HedgeRatioResponse:
    request = AnalyticsRequest(
        symbol_a=payload.symbol_a,
        symbol_b=payload.symbol_b,
        window=settings.analytics_window,
        timeframe="tick",
        include_intercept=payload.include_intercept,
    )
    analytics = await _compute(request, include_adf=False)
    return analytics.hedge_ratio


@router.post("/snapshot", response_model=AnalyticsResponse)
async def analytics_snapshot(request: AnalyticsRequest) -> AnalyticsResponse:
    return await _compute(request, include_adf=True)


@router.get("/adf", response_model=ADFPayload)
async def adf_test(
    symbol_a: str = Query(..., description="Primary symbol"),
    symbol_b: str = Query(..., description="Secondary symbol"),
    timeframe: str = Query("1s"),
    window: int = Query(300, ge=10, le=10_000),
) -> ADFPayload:
    request = AnalyticsRequest(
        symbol_a=symbol_a,
        symbol_b=symbol_b,
        timeframe=timeframe,
        window=window,
    )
    analytics = await _compute(request, include_adf=True)
    if analytics.adf is None:
        raise HTTPException(status_code=422, detail="ADF test could not be computed")
    return analytics.adf



