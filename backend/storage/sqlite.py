"""SQLite helpers for persisting tick and bar data."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterable, Iterator

from backend.core.config import settings
from backend.schemas.tick import Tick


def _db_path() -> Path:
    path = Path(settings.sqlite_path)
    if not path.is_absolute():
        data_dir = Path(settings.data_dir)
        data_dir.mkdir(parents=True, exist_ok=True)
        path = data_dir / path.name
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(_db_path())
    try:
        yield connection
    finally:
        connection.close()


def init_db() -> None:
    """Initialise database tables if they do not exist."""

    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ticks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                symbol TEXT NOT NULL,
                price REAL NOT NULL,
                size REAL NOT NULL
            )
            """
        )
        conn.commit()


def insert_ticks(ticks: Iterable[Tick]) -> int:
    """Bulk insert ticks into the database."""

    rows = [
        (tick.ts.isoformat(), tick.symbol, tick.price, tick.size)
        for tick in ticks
    ]
    if not rows:
        return 0

    with get_connection() as conn:
        conn.executemany(
            "INSERT INTO ticks (ts, symbol, price, size) VALUES (?, ?, ?, ?)", rows
        )
        conn.commit()
        return len(rows)


def fetch_recent_ticks(symbol: str, limit: int = 1000) -> list[Tick]:
    """Retrieve recent ticks for a symbol."""

    query = (
        "SELECT ts, symbol, price, size FROM ticks WHERE symbol = ? ORDER BY ts DESC LIMIT ?"
    )
    with get_connection() as conn:
        rows = conn.execute(query, (symbol, limit)).fetchall()

    ticks = [
        Tick(
            ts=datetime.fromisoformat(ts),
            symbol=symbol,
            price=price,
            size=size,
        )
        for ts, symbol, price, size in rows
    ]
    return list(reversed(ticks))



