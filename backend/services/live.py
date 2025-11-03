"""Live metrics stream derived from tick ingestion."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Set

from backend.core.config import settings
from backend.schemas import AlertEvent
from backend.services.metrics import compute_pair_metrics

LOGGER = logging.getLogger(__name__)


class LiveMetricsStream:
    """Broadcasts live metrics to subscribers and evaluates alerts."""

    def __init__(self, ingest_service, alert_manager) -> None:
        self._ingest_service = ingest_service
        self._alert_manager = alert_manager
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._tick_queue: Optional[asyncio.Queue] = None
        self._subscribers: Set[asyncio.Queue] = set()
        self._latest_payload: Optional[Dict[str, Any]] = None

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._tick_queue = asyncio.Queue(maxsize=2_000)
        self._ingest_service.add_subscriber(self._tick_queue)
        self._task = asyncio.create_task(self._run(), name="live-metrics")
        LOGGER.info("Live metrics stream started")

    async def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        if self._tick_queue is not None:
            self._ingest_service.remove_subscriber(self._tick_queue)
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        LOGGER.info("Live metrics stream stopped")

    async def _run(self) -> None:
        default_symbols = settings.default_symbols
        if len(default_symbols) < 2:
            LOGGER.warning("Not enough default symbols configured for live metrics")
            return
        sym_a, sym_b = default_symbols[:2]
        window = settings.analytics_window
        try:
            while self._running and self._tick_queue is not None:
                tick = await self._tick_queue.get()
                analytics, metrics_map = compute_pair_metrics(
                    self._ingest_service.buffer.snapshot(sym_a),
                    self._ingest_service.buffer.snapshot(sym_b),
                    window=window,
                    include_intercept=True,
                    adf=False,
                )

                alerts = self._alert_manager.evaluate(metrics_map)
                payload = self._build_payload(tick, analytics.dict(), alerts)
                self._latest_payload = payload
                await self._broadcast(payload)
        except asyncio.CancelledError:
            LOGGER.debug("Live metrics stream cancelled")

    async def _broadcast(self, payload: Dict[str, Any]) -> None:
        for subscriber in list(self._subscribers):
            if subscriber.full():
                continue
            try:
                subscriber.put_nowait(payload)
            except Exception:  # pragma: no cover - defensive
                self._subscribers.discard(subscriber)

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=200)
        if self._latest_payload is not None:
            queue.put_nowait(self._latest_payload)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        self._subscribers.discard(queue)

    def latest(self) -> Optional[Dict[str, Any]]:
        return self._latest_payload

    @staticmethod
    def _build_payload(tick, analytics: Dict[str, Any], alerts: list[AlertEvent]) -> Dict[str, Any]:
        return {
            "timestamp": tick.ts.isoformat() if hasattr(tick, "ts") else datetime.utcnow().isoformat(),
            "symbol": getattr(tick, "symbol", None),
            "price": getattr(tick, "price", None),
            "analytics": analytics,
            "alerts": [event.dict() for event in alerts],
        }


