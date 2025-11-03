"""Alert management and evaluation service."""

from __future__ import annotations

import logging
from collections import deque
from datetime import datetime
from typing import Deque, Dict, List
from uuid import UUID

from backend.schemas import Alert, AlertCreate, AlertEvent, AlertOperator

LOGGER = logging.getLogger(__name__)


class AlertManager:
    """Manage alert rules and evaluate metrics to emit events."""

    def __init__(self, history_limit: int = 500) -> None:
        self._alerts: Dict[UUID, Alert] = {}
        self._history: Deque[AlertEvent] = deque(maxlen=history_limit)

    def list_alerts(self) -> List[Alert]:
        return list(self._alerts.values())

    def get_alert(self, alert_id: UUID) -> Alert:
        return self._alerts[alert_id]

    def create_alert(self, payload: AlertCreate) -> Alert:
        alert = Alert(**payload.dict())
        self._alerts[alert.id] = alert
        LOGGER.info("Created alert %s (%s %s %s)", alert.name, alert.metric, alert.operator, alert.threshold)
        return alert

    def delete_alert(self, alert_id: UUID) -> None:
        if alert_id in self._alerts:
            del self._alerts[alert_id]

    def toggle_alert(self, alert_id: UUID, active: bool) -> Alert:
        alert = self._alerts[alert_id]
        alert.active = active
        return alert

    def history(self) -> List[AlertEvent]:
        return list(self._history)

    def evaluate(self, metrics: Dict[str, float]) -> List[AlertEvent]:
        triggered: List[AlertEvent] = []
        for alert in self._alerts.values():
            if not alert.active:
                continue
            value = metrics.get(alert.metric)
            if value is None:
                continue
            if self._compare(value, alert.operator, alert.threshold):
                event = AlertEvent(
                    alert_id=alert.id,
                    name=alert.name,
                    metric=alert.metric,
                    operator=alert.operator,
                    threshold=alert.threshold,
                    metric_value=value,
                    triggered_at=datetime.utcnow(),
                )
                alert.last_triggered = event.triggered_at
                self._history.appendleft(event)
                triggered.append(event)
        return triggered

    @staticmethod
    def _compare(value: float, operator: AlertOperator, threshold: float) -> bool:
        if operator == AlertOperator.greater:
            return value > threshold
        if operator == AlertOperator.greater_equal:
            return value >= threshold
        if operator == AlertOperator.less:
            return value < threshold
        if operator == AlertOperator.less_equal:
            return value <= threshold
        return False


