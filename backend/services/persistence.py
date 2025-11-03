"""Background task for persisting ticks to SQLite."""

from __future__ import annotations

import asyncio
import logging
from typing import List, Optional

from backend.core.config import settings
from backend.schemas.tick import Tick
from backend.storage import insert_ticks

LOGGER = logging.getLogger(__name__)


class TickPersistenceWorker:
    """Persist ticks from the ingest service into SQLite."""

    def __init__(self, queue_maxsize: int = 5_000) -> None:
        self.queue: asyncio.Queue[Tick] = asyncio.Queue(maxsize=queue_maxsize)
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._buffer: List[Tick] = []

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run(), name="tick-persistence")
        LOGGER.info("Tick persistence worker started")

    async def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self._flush(force=True)
        LOGGER.info("Tick persistence worker stopped")

    async def _run(self) -> None:
        flush_interval = settings.db_flush_interval_seconds
        batch_size = settings.db_batch_size
        try:
            while self._running:
                try:
                    tick = await asyncio.wait_for(self.queue.get(), timeout=flush_interval)
                    self._buffer.append(tick)
                    if len(self._buffer) >= batch_size:
                        await self._flush()
                except asyncio.TimeoutError:
                    if self._buffer:
                        await self._flush()
        except asyncio.CancelledError:
            LOGGER.debug("Persistence worker cancelled")
        finally:
            if self._buffer:
                await self._flush(force=True)

    async def _flush(self, force: bool = False) -> None:
        if not self._buffer:
            return
        batch = list(self._buffer)
        self._buffer.clear()
        written = insert_ticks(batch)
        LOGGER.debug("Flushed %s ticks to SQLite (force=%s)", written, force)


