"""
CrewAI telemetry callbacks.
Hooks into pipeline and stage lifecycle events to emit telemetry.
"""

from __future__ import annotations
import logging
from datetime import datetime
from models.telemetry import TelemetryEvent, EventType
from models.pipeline_state import PipelineState
from models.artifacts import StageID

logger = logging.getLogger(__name__)


class TelemetryCallbacks:
    def __init__(self, metrics_collector=None):
        self._collector = metrics_collector
        self._events: list[TelemetryEvent] = []
        self._stage_start_times: dict[str, datetime] = {}

    def on_pipeline_start(self, state: PipelineState):
        event = TelemetryEvent(
            pipeline_id=state.pipeline_id,
            event_type=EventType.PIPELINE_STARTED,
            data={"prd_id": state.prd_id, "feature_id": state.feature_id, "platform": state.platform}
        )
        self._emit(event)

    def on_pipeline_complete(self, state: PipelineState):
        event = TelemetryEvent(
            pipeline_id=state.pipeline_id,
            event_type=EventType.PIPELINE_COMPLETED,
            data=state.summary()
        )
        self._emit(event)

    def on_pipeline_fail(self, state: PipelineState, error: str):
        event = TelemetryEvent(
            pipeline_id=state.pipeline_id,
            event_type=EventType.PIPELINE_FAILED,
            data={**state.summary(), "error": error}
        )
        self._emit(event)

    def on_stage_start(self, pipeline_id: str, stage_id: StageID):
        key = f"{pipeline_id}_{stage_id}"
        self._stage_start_times[key] = datetime.utcnow()
        event = TelemetryEvent(
            pipeline_id=pipeline_id,
            stage_id=stage_id,
            event_type=EventType.STAGE_STARTED,
            data={"stage_id": str(stage_id)}
        )
        self._emit(event)

    def on_stage_complete(self, pipeline_id: str, stage_id: StageID):
        key = f"{pipeline_id}_{stage_id}"
        duration_ms = None
        if key in self._stage_start_times:
            duration_ms = (datetime.utcnow() - self._stage_start_times.pop(key)).total_seconds() * 1000

        event = TelemetryEvent(
            pipeline_id=pipeline_id,
            stage_id=stage_id,
            event_type=EventType.STAGE_COMPLETED,
            duration_ms=duration_ms,
            data={"stage_id": str(stage_id)}
        )
        self._emit(event)

    def on_stage_retry(self, pipeline_id: str, stage_id: StageID, attempt: int, error: str):
        event = TelemetryEvent(
            pipeline_id=pipeline_id,
            stage_id=stage_id,
            event_type=EventType.STAGE_RETRIED,
            data={"attempt": attempt, "error": error}
        )
        self._emit(event)

    def on_approval_requested(self, pipeline_id: str, stage_id: StageID, approval_id: str):
        event = TelemetryEvent(
            pipeline_id=pipeline_id,
            stage_id=stage_id,
            event_type=EventType.APPROVAL_REQUESTED,
            data={"approval_id": approval_id}
        )
        self._emit(event)

    def get_events(self, pipeline_id: str) -> list[TelemetryEvent]:
        return [e for e in self._events if e.pipeline_id == pipeline_id]

    def _emit(self, event: TelemetryEvent):
        self._events.append(event)
        logger.info("[TELEMETRY] %s | %s | %s", event.pipeline_id, event.event_type, event.data)
        if self._collector:
            self._collector.record(event)
