"""Core quantitative analytics helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller


@dataclass(slots=True)
class HedgeRatioResult:
    """Container for hedge ratio regression outputs."""

    beta: float
    intercept: Optional[float]
    rvalue: Optional[float]
    pvalue: Optional[float]
    stderr: Optional[float]


@dataclass(slots=True)
class ADFResult:
    """Augmented Dickey-Fuller test summary."""

    statistic: float
    pvalue: float
    lags: int
    nobs: int
    critical_values: dict[str, float]


def _align_series(series_a: pd.Series, series_b: pd.Series) -> pd.DataFrame:
    """Align two series on the same index and drop missing values."""
    
    # Ensure both series have datetime index for proper alignment
    if not isinstance(series_a.index, pd.DatetimeIndex):
        raise ValueError("Series A must have a DatetimeIndex")
    if not isinstance(series_b.index, pd.DatetimeIndex):
        raise ValueError("Series B must have a DatetimeIndex")
    
    # Convert to DataFrames for merge_asof
    df_a = series_a.to_frame("asset_a").reset_index()
    df_b = series_b.to_frame("asset_b").reset_index()
    
    # Use merge_asof to align with 1-second tolerance
    # This matches each timestamp in A with the nearest timestamp in B within 1 second
    merged = pd.merge_asof(
        df_a.sort_values("ts"),
        df_b.sort_values("ts"),
        on="ts",
        direction="nearest",
        tolerance=pd.Timedelta(seconds=1),
        suffixes=("", "_b")
    )
    
    # Set timestamp as index and drop missing values
    merged.set_index("ts", inplace=True)
    aligned = merged[["asset_a", "asset_b"]].dropna(how="any")
    
    # Require minimum overlap for meaningful regression
    if len(aligned) < 10:
        raise ValueError(f"Insufficient overlapping data points: {len(aligned)} (need at least 10)")
    
    return aligned


def compute_hedge_ratio(
    series_a: pd.Series,
    series_b: pd.Series,
    include_intercept: bool = True,
) -> HedgeRatioResult:
    """Estimate the hedge ratio beta between two price series via OLS."""

    aligned = _align_series(series_a, series_b)
    if aligned.empty:
        raise ValueError("No overlapping observations between the provided series.")

    y = aligned["asset_a"]
    x = aligned["asset_b"]

    if include_intercept:
        X = sm.add_constant(x)
    else:
        X = x.to_numpy().reshape(-1, 1)

    model = sm.OLS(y, X).fit()

    if include_intercept:
        intercept = float(model.params.iloc[0])
        beta = float(model.params.iloc[1])
    else:
        intercept = None
        beta = float(model.params.iloc[0])

    rvalue = float(np.sqrt(model.rsquared)) if model.rsquared is not None else None
    pvalue = float(model.pvalues.iloc[1] if include_intercept else model.pvalues.iloc[0])
    stderr = float(model.bse.iloc[1] if include_intercept else model.bse.iloc[0])

    # Validation: Check for suspicious values
    # If R-squared is very low (< 0.1), the regression fit is poor
    # If intercept is extremely large relative to prices, there's likely data misalignment
    mean_price_a = float(y.mean())
    mean_price_b = float(x.mean())
    
    is_suspicious = False
    if rvalue is not None and rvalue < 0.3:  # Low correlation suggests poor fit
        is_suspicious = True
    if intercept is not None and abs(intercept) > abs(mean_price_a) * 10:  # Intercept too large
        is_suspicious = True
    if abs(beta) > 1000:  # Hedge ratio is extremely large
        is_suspicious = True
    
    # Note: Negative beta is valid if assets move in opposite directions
    # But for BTC/ETH pairs, it's unusual and may indicate data issues

    return HedgeRatioResult(
        beta=beta,
        intercept=intercept,
        rvalue=rvalue,
        pvalue=pvalue,
        stderr=stderr,
    )


def compute_spread(
    series_a: pd.Series,
    series_b: pd.Series,
    hedge_ratio: HedgeRatioResult,
) -> pd.Series:
    """Calculate the spread given the hedge ratio."""

    aligned = _align_series(series_a, series_b)
    spread = aligned["asset_a"] - hedge_ratio.beta * aligned["asset_b"]
    if hedge_ratio.intercept is not None:
        spread -= hedge_ratio.intercept
    return spread


def compute_zscore(spread: pd.Series, window: int) -> pd.Series:
    """Return the rolling z-score of the spread."""

    if window <= 1:
        raise ValueError("Rolling window must be greater than 1.")

    # Use min_periods=2 to allow partial calculations with less data
    min_periods = min(2, window)
    rolling_mean = spread.rolling(window=window, min_periods=min_periods).mean()
    rolling_std = spread.rolling(window=window, min_periods=min_periods).std()
    zscore = (spread - rolling_mean) / rolling_std
    # Only drop where std is zero (division by zero) or truly NaN
    return zscore[rolling_std > 0].dropna()


def compute_rolling_correlation(
    series_a: pd.Series,
    series_b: pd.Series,
    window: int,
) -> pd.Series:
    """Compute rolling Pearson correlation between two series."""

    if window <= 1:
        raise ValueError("Rolling window must be greater than 1.")

    aligned = _align_series(series_a, series_b)
    # Use min_periods=2 to allow partial calculations with less data
    min_periods = min(2, window)
    return aligned["asset_a"].rolling(window, min_periods=min_periods).corr(aligned["asset_b"])


def compute_adf(spread: pd.Series, max_lag: Optional[int] = None) -> ADFResult:
    """Run an Augmented Dickey-Fuller test on the spread series."""

    clean_spread = spread.dropna()
    if clean_spread.empty:
        raise ValueError("Spread series is empty.")

    statistic, pvalue, usedlag, nobs, critical_values, _ = adfuller(
        clean_spread, maxlag=max_lag, autolag="AIC"
    )

    return ADFResult(
        statistic=float(statistic),
        pvalue=float(pvalue),
        lags=int(usedlag),
        nobs=int(nobs),
        critical_values={str(k): float(v) for k, v in critical_values.items()},
    )


