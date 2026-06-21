"""Telemetry and observability models."""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid

from .artifacts import StageID


class EventType(str, Enum):
    PIPELINE_STARTED = "pipeline_started"
    PIPELINE_COMPLETED = "pipeline_completed"
    PIPELINE_FAILED = "pipeline_failed"
    STAGE_STARTED = "stage_started"
    STAGE_COMPLETED = "stage_completed"
    STAGE_FAILED = "stage_failed"
    STAGE_RETRIED = "stage_retried"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_REJECTED = "approval_rejected"
    ARTIFACT_STORED = "artifact_stored"
    CHECKPOINT_CREATED = "checkpoint_created"
    TRIAGE_LOOP_STARTED = "triage_loop_started"
    TRIAGE_LOOP_COMPLETED = "triage_loop_completed"


class TelemetryEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pipeline_id: str
    stage_id: Optional[StageID] = None
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(default_factory=dict)
    duration_ms: Optional[float] = None
    token_usage: Optional[Dict[str, int]] = None
    error: Optional[str] = None

    class Config:
        use_enum_values = True


class StageMetrics(BaseModel):
    stage_id: StageID
    pipeline_id: str
    duration_seconds: float
    retry_count: int = 0
    token_input: int = 0
    token_output: int = 0
    artifacts_produced: int = 0
    success: bool = True
    error_type: Optional[str] = None

    class Config:
        use_enum_values = True


class PipelineMetrics(BaseModel):
    pipeline_id: str
    platform: str
    total_duration_seconds: float
    stage_metrics: List[StageMetrics] = Field(default_factory=list)
    total_token_input: int = 0
    total_token_output: int = 0
    triage_loop_count: int = 0
    stages_completed: int = 0
    stages_failed: int = 0
    success: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
