"""Metrics aggregation from telemetry events."""

from __future__ import annotations

from collections import defaultdict

from models.telemetry import EventType, PipelineMetrics, StageMetrics, TelemetryEvent


class MetricsCollector:
    def __init__(self):
        self._raw: list[TelemetryEvent] = []

    def record(self, event: TelemetryEvent):
        self._raw.append(event)

    def pipeline_metrics(self, pipeline_id: str) -> PipelineMetrics:
        events = [e for e in self._raw if e.pipeline_id == pipeline_id]

        start = next((e for e in events if e.event_type == EventType.PIPELINE_STARTED), None)
        end = next(
            (
                e
                for e in events
                if e.event_type in (EventType.PIPELINE_COMPLETED, EventType.PIPELINE_FAILED)
            ),
            None,
        )

        total_duration = 0.0
        if start and end:
            total_duration = (end.timestamp - start.timestamp).total_seconds()

        stage_starts: dict[str, TelemetryEvent] = {}
        stage_ends: dict[str, TelemetryEvent] = {}
        stage_retries: dict[str, int] = defaultdict(int)

        for e in events:
            sid = str(e.stage_id) if e.stage_id else ""
            if e.event_type == EventType.STAGE_STARTED:
                stage_starts[sid] = e
            elif e.event_type == EventType.STAGE_COMPLETED:
                stage_ends[sid] = e
            elif e.event_type == EventType.STAGE_RETRIED:
                stage_retries[sid] += 1

        stage_metrics = []
        for sid, s_event in stage_starts.items():
            e_event = stage_ends.get(sid)
            duration = 0.0
            if e_event:
                duration = (e_event.timestamp - s_event.timestamp).total_seconds()
            stage_metrics.append(
                StageMetrics(
                    stage_id=s_event.stage_id,
                    pipeline_id=pipeline_id,
                    duration_seconds=duration,
                    retry_count=stage_retries.get(sid, 0),
                    success=sid in stage_ends,
                )
            )

        triage_loop = next(
            (
                e.data.get("triage_loop_count", 0)
                for e in events
                if e.event_type == EventType.PIPELINE_COMPLETED
            ),
            0,
        )

        return PipelineMetrics(
            pipeline_id=pipeline_id,
            platform="",
            total_duration_seconds=total_duration,
            stage_metrics=stage_metrics,
            stages_completed=sum(1 for s in stage_metrics if s.success),
            stages_failed=sum(1 for s in stage_metrics if not s.success),
            triage_loop_count=triage_loop,
            success=end is not None and end.event_type == EventType.PIPELINE_COMPLETED,
        )

    def summary_report(self, pipeline_id: str) -> dict:
        m = self.pipeline_metrics(pipeline_id)
        return {
            "pipeline_id": m.pipeline_id,
            "success": m.success,
            "total_duration_seconds": m.total_duration_seconds,
            "stages_completed": m.stages_completed,
            "stages_failed": m.stages_failed,
            "triage_loop_count": m.triage_loop_count,
            "slowest_stage": max(m.stage_metrics, key=lambda s: s.duration_seconds, default=None),
            "most_retried_stage": max(m.stage_metrics, key=lambda s: s.retry_count, default=None),
        }
