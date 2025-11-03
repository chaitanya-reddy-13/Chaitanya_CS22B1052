"""Helpers to compute live analytics metrics from in-memory buffers."""

from __future__ import annotations

from typing import Dict, Tuple

import pandas as pd

from backend.analytics import (
    compute_adf,
    compute_hedge_ratio,
    compute_rolling_correlation,
    compute_spread,
    compute_zscore,
    resample_ohlcv,
    ticks_to_dataframe,
)
from backend.schemas import ADFPayload, AnalyticsResponse, HedgeRatioResponse


def _price_series(ticks) -> pd.Series:
    df = ticks_to_dataframe(ticks)
    if df.empty:
        return pd.Series(dtype="float64")
    return df["price"].astype(float)


def compute_pair_metrics(
    ticks_a,
    ticks_b,
    *,
    window: int,
    include_intercept: bool,
    adf: bool = False,
) -> Tuple[AnalyticsResponse, Dict[str, float]]:
    """Compute analytics payload and raw metric map for alerts."""

    series_a = _price_series(ticks_a)
    series_b = _price_series(ticks_b)

    if series_a.empty or series_b.empty:
        return (
            AnalyticsResponse(
                hedge_ratio=HedgeRatioResponse(
                    beta=0.0, intercept=0.0, rvalue=None, pvalue=None, stderr=None
                ),
                latest_spread=None,
                latest_zscore=None,
                rolling_correlation=None,
                adf=None,
            ),
            {},
        )

    hedge = compute_hedge_ratio(series_a, series_b, include_intercept)
    spread = compute_spread(series_a, series_b, hedge)
    
    # Ensure we have enough data for rolling calculations
    effective_window = min(window, len(spread))
    if effective_window < 2:
        effective_window = 2
    
    zscore = compute_zscore(spread, effective_window) if len(spread) >= 2 else pd.Series(dtype="float64")
    corr = compute_rolling_correlation(series_a, series_b, effective_window) if len(series_a) >= 2 and len(series_b) >= 2 else pd.Series(dtype="float64")

    adf_payload = None
    if adf and len(spread) >= 10:  # ADF needs sufficient data
        try:
            adf_payload = compute_adf(spread)
        except (ValueError, Exception):  # pragma: no cover - defensive
            pass

    # Get latest non-null values
    latest_spread = None
    if not spread.empty:
        valid_spread = spread.dropna()
        if not valid_spread.empty:
            latest_spread = float(valid_spread.iloc[-1])
    
    latest_zscore = None
    if not zscore.empty:
        valid_zscore = zscore.dropna()
        if not valid_zscore.empty:
            latest_zscore = float(valid_zscore.iloc[-1])
    
    latest_corr = None
    if not corr.empty:
        valid_corr = corr.dropna()
        if not valid_corr.empty:
            latest_corr = float(valid_corr.iloc[-1])

    analytics = AnalyticsResponse(
        hedge_ratio=HedgeRatioResponse(
            beta=hedge.beta,
            intercept=hedge.intercept,
            rvalue=hedge.rvalue,
            pvalue=hedge.pvalue,
            stderr=hedge.stderr,
        ),
        latest_spread=latest_spread,
        latest_zscore=latest_zscore,
        rolling_correlation=latest_corr,
        adf=ADFPayload(
            statistic=adf_payload.statistic,
            pvalue=adf_payload.pvalue,
            lags=adf_payload.lags,
            nobs=adf_payload.nobs,
            critical_values=adf_payload.critical_values,
        ) if adf_payload else None,
    )

    metrics_map = {
        "spread": analytics.latest_spread,
        "zscore": analytics.latest_zscore,
        "correlation": analytics.rolling_correlation,
        "beta": analytics.hedge_ratio.beta,
    }

    return analytics, {k: v for k, v in metrics_map.items() if v is not None}


def resample_ticks(ticks, timeframe: str) -> pd.DataFrame:
    df = ticks_to_dataframe(ticks)
    return resample_ohlcv(df, timeframe)


