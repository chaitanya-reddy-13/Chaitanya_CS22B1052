"""Alert schemas for creating and listing alert rules."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class AlertOperator(str, Enum):
    greater = ">"
    greater_equal = ">="
    less = "<"
    less_equal = "<="


class AlertCreate(BaseModel):
    name: str = Field(..., description="Friendly alert name")
    metric: str = Field(..., description="Metric key e.g. zscore, spread")
    operator: AlertOperator = AlertOperator.greater
    threshold: float = Field(..., description="Threshold to compare against")
    symbols: List[str] = Field(default_factory=list)
    window: Optional[int] = Field(
        default=None,
        description="Optional rolling window override for metric evaluation",
    )

    @validator("symbols", each_item=True)
    def lower_symbols(cls, value: str) -> str:
        return value.lower()


class Alert(AlertCreate):
    id: UUID = Field(default_factory=uuid4)
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_triggered: Optional[datetime] = None


class AlertEvent(BaseModel):
    alert_id: UUID
    name: str
    metric: str
    operator: AlertOperator
    threshold: float
    metric_value: float
    triggered_at: datetime = Field(default_factory=datetime.utcnow)


class AlertListResponse(BaseModel):
    alerts: List[Alert]


class AlertHistoryResponse(BaseModel):
    events: List[AlertEvent]


