"""Application configuration utilities."""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    app_name: str = "Binance Analytics Backend"
    backend_cors_origins: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )
    data_dir: str = "data"
    sqlite_path: str = "data/ticks.db"
    log_level: str = "INFO"
    default_symbols: List[str] = Field(default_factory=lambda: ["btcusdt", "ethusdt"])
    tick_buffer_size: int = 3_600
    db_flush_interval_seconds: float = 2.0
    db_batch_size: int = 200
    analytics_window: int = 300
    websocket_broadcast_interval: float = 0.5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""

    return Settings()


settings = get_settings()



