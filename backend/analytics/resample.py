"""Utilities for turning tick data into OHLCV bars."""

from __future__ import annotations

from typing import Iterable, Union

import pandas as pd

from backend.schemas.tick import Tick


def ticks_to_dataframe(ticks: Iterable[Union[dict, Tick]]) -> pd.DataFrame:
    """Convert ticks to a pandas DataFrame indexed by timestamp."""

    records = []
    for tick in ticks:
        if isinstance(tick, Tick):
            records.append(tick.dict())
        else:
            records.append(tick)

    df = pd.DataFrame.from_records(records)
    if df.empty:
        return df

    df = df.copy()
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    df.set_index("ts", inplace=True)
    return df.sort_index()


def resample_ohlcv(
    df: pd.DataFrame,
    timeframe: str,
    price_column: str = "price",
    size_column: str = "size",
) -> pd.DataFrame:
    """Resample tick dataframe into OHLCV bars."""

    if df.empty:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

    ohlc = df[price_column].resample(timeframe).ohlc()
    volume = df[size_column].resample(timeframe).sum().rename("volume")
    result = pd.concat([ohlc, volume], axis=1)
    return result.dropna(how="all")



