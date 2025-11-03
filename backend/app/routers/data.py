"""Data access endpoints for ticks and resampled bars."""

from __future__ import annotations

import io
from datetime import datetime
from typing import List

import pandas as pd
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

from backend.schemas import HistoryResponse, OHLCBar
from backend.services import ingest_service, resample_ticks
from backend.storage import fetch_recent_ticks

router = APIRouter()


TIMEFRAME_MAP = {
    "1s": "1s",
    "1m": "1Min",
    "5m": "5Min",
}


def _resolve_timeframe(timeframe: str) -> str:
    tf = TIMEFRAME_MAP.get(timeframe.lower())
    if not tf:
        raise HTTPException(status_code=400, detail=f"Unsupported timeframe '{timeframe}'")
    return tf


def _bars_from_dataframe(df: pd.DataFrame) -> List[OHLCBar]:
    bars: List[OHLCBar] = []
    for ts, row in df.iterrows():
        if row.isna().all():
            continue
        bars.append(
            OHLCBar(
                ts=ts.to_pydatetime() if hasattr(ts, "to_pydatetime") else datetime.fromisoformat(str(ts)),
                open=float(row["open"]) if pd.notna(row["open"]) else 0.0,
                high=float(row["high"]) if pd.notna(row["high"]) else 0.0,
                low=float(row["low"]) if pd.notna(row["low"]) else 0.0,
                close=float(row["close"]) if pd.notna(row["close"]) else 0.0,
                volume=float(row.get("volume", 0.0) or 0.0) if pd.notna(row.get("volume", 0.0)) else 0.0,
            )
        )
    return bars


@router.get("/history", response_model=HistoryResponse)
async def history(
    symbol: str = Query(..., description="Symbol to fetch"),
    timeframe: str = Query("1s", regex="^(1s|1m|5m)$"),
    limit: int = Query(3000, ge=10, le=50_000),
) -> HistoryResponse:
    symbol = symbol.lower()
    await ingest_service.add_symbol(symbol)
    ticks = fetch_recent_ticks(symbol, limit=limit)
    if not ticks:
        return HistoryResponse(symbol=symbol, timeframe=timeframe, bars=[])

    df = resample_ticks(ticks, _resolve_timeframe(timeframe))
    bars = _bars_from_dataframe(df.tail(limit))
    return HistoryResponse(symbol=symbol, timeframe=timeframe, bars=bars)


@router.get("/export")
async def export(
    symbol: str = Query(...), timeframe: str = Query("1s"), limit: int = Query(5000, ge=10, le=100_000)
):
    symbol = symbol.lower()
    await ingest_service.add_symbol(symbol)
    ticks = fetch_recent_ticks(symbol, limit=limit)
    if not ticks:
        raise HTTPException(status_code=404, detail="No data available for export")

    df = resample_ticks(ticks, _resolve_timeframe(timeframe)).reset_index()
    buffer = io.StringIO()
    df.rename(columns={"index": "ts"}, inplace=True)
    df.to_csv(buffer, index=False)
    buffer.seek(0)

    filename = f"{symbol}_{timeframe}_{datetime.utcnow().isoformat().replace(':', '-')}.csv"
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    return StreamingResponse(buffer, media_type="text/csv", headers=headers)


@router.post("/upload", response_model=HistoryResponse)
async def upload(
    file: UploadFile = File(...),
    timeframe: str = Query("1s", regex="^(1s|1m|5m)$"),
    symbol: str | None = Query(None, description="Optional symbol override"),
) -> HistoryResponse:
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as exc:  # pragma: no cover - pandas parsing error
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {exc}") from exc

    timestamp_col = next((col for col in ("ts", "timestamp", "time") if col in df.columns), None)
    if not timestamp_col:
        raise HTTPException(status_code=400, detail="CSV must include a 'ts' or 'timestamp' column")

    df["ts"] = pd.to_datetime(df[timestamp_col], utc=True)
    if "price" not in df.columns and "close" in df.columns:
        df["price"] = df["close"]
    if "price" not in df.columns:
        raise HTTPException(status_code=400, detail="CSV must include a 'price' or 'close' column")

    if "size" not in df.columns:
        df["size"] = df.get("volume", 0.0)

    if "symbol" not in df.columns:
        if not symbol:
            raise HTTPException(status_code=400, detail="Provide symbol query param when CSV lacks 'symbol' column")
        df["symbol"] = symbol.lower()
    else:
        df["symbol"] = df["symbol"].str.lower()

    target_symbol = (symbol or df["symbol"].iloc[0]).lower()
    filtered = df[df["symbol"] == target_symbol]
    if filtered.empty:
        raise HTTPException(status_code=400, detail="No rows matched the provided symbol")

    ticks = filtered[["ts", "symbol", "price", "size"]].to_dict("records")
    df_resampled = resample_ticks(ticks, _resolve_timeframe(timeframe))
    bars = _bars_from_dataframe(df_resampled)

    return HistoryResponse(symbol=target_symbol, timeframe=timeframe, bars=bars)



