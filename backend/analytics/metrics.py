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

    # Require minimum data points for reliable regression
    if len(aligned) < 50:
        raise ValueError(f"Insufficient data for regression: {len(aligned)} points (need at least 50)")

    y = aligned["asset_a"]
    x = aligned["asset_b"]

    # Check for reasonable price ranges (prevent division by zero or extreme values)
    if y.min() <= 0 or x.min() <= 0:
        raise ValueError("Price series contains non-positive values")
    
    mean_a, mean_b = float(y.mean()), float(x.mean())
    std_a, std_b = float(y.std()), float(x.std())
    
    # Check for reasonable price scales (prevent extreme outliers from corrupting regression)
    if std_a > mean_a * 10 or std_b > mean_b * 10:
        raise ValueError("Price series has extreme variance, likely data quality issue")

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

    # Validation: Check for suspicious values and raise warning
    # For typical BTC/ETH: BTC ~100k, ETH ~3.5k, so beta should be ~28.5 (regressing BTC on ETH)
    # Or if we regress ETH on BTC: beta ~0.035
    # But absolute value > 1000 is definitely wrong
    if abs(beta) > 1000:
        # If beta is extremely large, the regression is likely wrong
        # Try the reverse regression as a sanity check
        if include_intercept:
            X_reverse = sm.add_constant(y)
        else:
            X_reverse = y.to_numpy().reshape(-1, 1)
        model_reverse = sm.OLS(x, X_reverse).fit()
        beta_reverse = float(model_reverse.params.iloc[1] if include_intercept else model_reverse.params.iloc[0])
        
        # If reverse beta is reasonable, use it (regression direction was wrong)
        if 0 < abs(beta_reverse) < 1000:
            # Use 1/beta_reverse as the hedge ratio
            beta = 1.0 / beta_reverse if beta_reverse != 0 else beta
            intercept = None if not include_intercept else float(model_reverse.params.iloc[0])
            rvalue = float(np.sqrt(model_reverse.rsquared)) if model_reverse.rsquared is not None else None
            pvalue = float(model_reverse.pvalues.iloc[1] if include_intercept else model_reverse.pvalues.iloc[0])
            stderr = float(model_reverse.bse.iloc[1] if include_intercept else model_reverse.bse.iloc[0])

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


