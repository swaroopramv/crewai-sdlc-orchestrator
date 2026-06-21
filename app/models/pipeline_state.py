"""Pipeline state models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .artifacts import StageID


class PipelineStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    AWAITING_APPROVAL = "awaiting_approval"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class StageStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    AWAITING_APPROVAL = "awaiting_approval"


class StageRun(BaseModel):
    stage_id: StageID
    status: StageStatus = StageStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    retry_count: int = 0
    error: Optional[str] = None
    input_artifact_ids: List[str] = Field(default_factory=list)
    output_artifact_ids: List[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True

    def start(self):
        self.status = StageStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()

    def complete(self, output_artifact_ids: List[str]):
        self.status = StageStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.output_artifact_ids = output_artifact_ids
        if self.started_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds()

    def fail(self, error: str):
        self.status = StageStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error = error
        if self.started_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds()

    def reset_for_retry(self):
        self.status = StageStatus.PENDING
        self.retry_count += 1
        self.started_at = None
        self.completed_at = None
        self.error = None


class PipelineState(BaseModel):
    pipeline_id: str
    prd_id: str
    feature_id: str
    platform: str
    status: PipelineStatus = PipelineStatus.NOT_STARTED
    current_stage_id: Optional[StageID] = None
    stages: Dict[str, StageRun] = Field(default_factory=dict)
    triage_loop_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Config:
        use_enum_values = True

    def get_stage(self, stage_id: StageID) -> StageRun:
        key = stage_id.value if hasattr(stage_id, "value") else stage_id
        if key not in self.stages:
            self.stages[key] = StageRun(stage_id=stage_id)
        return self.stages[key]

    def mark_started(self, stage_id: StageID):
        stage = self.get_stage(stage_id)
        stage.start()
        self.current_stage_id = stage_id
        self.status = PipelineStatus.IN_PROGRESS
        self.updated_at = datetime.utcnow()

    def mark_completed(self, stage_id: StageID, output_ids: List[str]):
        stage = self.get_stage(stage_id)
        stage.complete(output_ids)
        self.updated_at = datetime.utcnow()

    def mark_failed(self, stage_id: StageID, error: str):
        stage = self.get_stage(stage_id)
        stage.fail(error)
        self.status = PipelineStatus.FAILED
        self.updated_at = datetime.utcnow()

    def reset_stage_for_retry(self, stage_id: StageID):
        stage = self.get_stage(stage_id)
        stage.reset_for_retry()
        self.updated_at = datetime.utcnow()

    def get_last_completed_stage(self) -> Optional[StageID]:
        completed = [s for s in self.stages.values() if s.status == StageStatus.COMPLETED]
        if not completed:
            return None
        return sorted(completed, key=lambda x: x.completed_at or datetime.min)[-1].stage_id

    def summary(self) -> Dict:
        return {
            "pipeline_id": self.pipeline_id,
            "status": self.status,
            "current_stage": self.current_stage_id,
            "total_stages": len(self.stages),
            "completed_stages": sum(
                1 for s in self.stages.values() if s.status == StageStatus.COMPLETED
            ),
            "failed_stages": sum(1 for s in self.stages.values() if s.status == StageStatus.FAILED),
            "triage_loop_count": self.triage_loop_count,
        }
