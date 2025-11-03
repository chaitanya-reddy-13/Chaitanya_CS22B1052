"""Service singletons used by the FastAPI application."""

from backend.core.config import settings
from backend.services.alerts import AlertManager
from backend.services.ingest import BinanceIngestService
from backend.services.live import LiveMetricsStream
from backend.services.metrics import compute_pair_metrics, resample_ticks
from backend.services.persistence import TickPersistenceWorker


ingest_service = BinanceIngestService(
    symbols=settings.default_symbols,
    buffer_size=settings.tick_buffer_size,
)

persistence_worker = TickPersistenceWorker()

alert_manager = AlertManager()

live_metrics_stream = LiveMetricsStream(ingest_service, alert_manager)


__all__ = [
    "ingest_service",
    "persistence_worker",
    "alert_manager",
    "live_metrics_stream",
    "compute_pair_metrics",
    "resample_ticks",
]


