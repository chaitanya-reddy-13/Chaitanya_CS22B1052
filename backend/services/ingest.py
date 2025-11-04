"""Binance WebSocket ingestion service."""

from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import AsyncIterator, Deque, Dict, Iterable, Optional, Set

import websockets

from backend.schemas.tick import Tick

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class TickBuffer:
    """In-memory hot store for recent ticks per symbol."""

    maxlen: int
    data: Dict[str, Deque[Tick]] = field(init=False)

    def __post_init__(self) -> None:
        self.data = defaultdict(self._deque_factory)

    def _deque_factory(self) -> Deque[Tick]:
        return deque(maxlen=self.maxlen)

    def configure(self, symbols: Iterable[str]) -> None:
        for symbol in symbols:
            self.ensure_symbol(symbol)

    def ensure_symbol(self, symbol: str) -> None:
        if symbol not in self.data:
            self.data[symbol] = self._deque_factory()

    def append(self, tick: Tick) -> None:
        self.ensure_symbol(tick.symbol)
        self.data[tick.symbol].append(tick)

    def snapshot(self, symbol: str) -> list[Tick]:
        return list(self.data.get(symbol, []))


class BinanceIngestService:
    """Manage WebSocket connections to Binance Futures trade streams."""

    def __init__(
        self,
        symbols: Optional[Iterable[str]] = None,
        *,
        queue: Optional[asyncio.Queue[Tick]] = None,
        buffer_size: int = 3_600,
        reconnect_delay: float = 5.0,
    ) -> None:
        self.symbols = {s.lower() for s in (symbols or [])}
        self.queue: asyncio.Queue[Tick] = queue or asyncio.Queue()
        self.buffer = TickBuffer(maxlen=buffer_size)
        self.buffer.configure(self.symbols)
        self.reconnect_delay = reconnect_delay
        self._tasks: set[asyncio.Task] = set()
        self._running = asyncio.Event()
        self._subscribers: Set[asyncio.Queue[Tick]] = set()

    def update_symbols(self, symbols: Iterable[str]) -> None:
        self.symbols = {s.lower() for s in symbols}
        self.buffer.configure(self.symbols)

    async def add_symbol(self, symbol: str) -> None:
        symbol = symbol.lower()
        if symbol in self.symbols:
            return
        self.symbols.add(symbol)
        self.buffer.ensure_symbol(symbol)
        if self._running.is_set():
            task = asyncio.create_task(self._consume_symbol(symbol), name=f"ws:{symbol}")
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)

    async def start(self) -> None:
        if self._running.is_set():
            LOGGER.info("Ingest service already running")
            return

        self._running.set()
        LOGGER.info("Starting ingest service for %s", ", ".join(sorted(self.symbols)))
        for symbol in self.symbols:
            task = asyncio.create_task(self._consume_symbol(symbol), name=f"ws:{symbol}")
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)

    async def stop(self) -> None:
        if not self._running.is_set():
            return
        self._running.clear()
        LOGGER.info("Stopping ingest service")
        for task in list(self._tasks):
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

    async def _consume_symbol(self, symbol: str) -> None:
        url = f"wss://fstream.binance.com/ws/{symbol}@trade"
        while self._running.is_set():
            try:
                # Add timeout to prevent hanging during connection (10 second timeout)
                websocket = await asyncio.wait_for(
                    websockets.connect(url, ping_interval=20, ping_timeout=10),
                    timeout=10.0
                )
                async with websocket:
                    LOGGER.info("Connected to %s", url)
                    async for message in websocket:
                        if not self._running.is_set():
                            break
                        tick = self._parse_message(symbol, message)
                        if tick is None:
                            continue
                        self.buffer.append(tick)
                        await self.queue.put(tick)
                        await self._broadcast(tick)
            except asyncio.TimeoutError:
                LOGGER.warning("WebSocket connection timeout for %s, retrying...", symbol)
                await asyncio.sleep(self.reconnect_delay)
            except asyncio.CancelledError:
                LOGGER.debug("WebSocket task for %s cancelled", symbol)
                break
            except Exception as exc:  # pylint: disable=broad-except
                LOGGER.warning("WebSocket error for %s: %s", symbol, exc)
                await asyncio.sleep(self.reconnect_delay)

    @staticmethod
    def _parse_message(symbol: str, message: str) -> Optional[Tick]:
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            LOGGER.debug("Failed to decode message for %s", symbol)
            return None

        if payload.get("e") != "trade":
            return None

        ts_ms = payload.get("T") or payload.get("E")
        if ts_ms is None:
            return None

        ts = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
        price = float(payload.get("p"))
        quantity = float(payload.get("q"))

        return Tick(symbol=symbol, ts=ts, price=price, size=quantity)

    async def stream(self) -> AsyncIterator[Tick]:
        """Yield ticks as they arrive from the primary queue."""

        while True:
            tick = await self.queue.get()
            yield tick

    def add_subscriber(self, subscriber_queue: asyncio.Queue[Tick]) -> None:
        self._subscribers.add(subscriber_queue)

    def remove_subscriber(self, subscriber_queue: asyncio.Queue[Tick]) -> None:
        self._subscribers.discard(subscriber_queue)

    async def _broadcast(self, tick: Tick) -> None:
        stale_subscribers: set[asyncio.Queue[Tick]] = set()
        for subscriber in self._subscribers:
            if subscriber.full():
                LOGGER.debug("Dropping tick for slow subscriber")
                continue
            try:
                subscriber.put_nowait(tick)
            except Exception as exc:  # pragma: no cover - defensive
                LOGGER.debug("Subscriber queue error: %s", exc)
                stale_subscribers.add(subscriber)

        for stale in stale_subscribers:
            self._subscribers.discard(stale)



