"""Pipeline state manager — persists and restores PipelineState via the checkpoint store."""

from __future__ import annotations

from typing import Optional

from models.artifacts import StageID
from models.pipeline_state import PipelineState, StageStatus
from storage.checkpoint_store import CheckpointStore


class StateManager:
    def __init__(self, checkpoint_store: CheckpointStore):
        self._store = checkpoint_store
        self._cache: dict[str, PipelineState] = {}

    def init_state(self, pipeline_id: str, prd_id: str, feature_id: str, platform: str) -> PipelineState:
        state = PipelineState(
            pipeline_id=pipeline_id,
            prd_id=prd_id,
            feature_id=feature_id,
            platform=platform,
        )
        self._cache[pipeline_id] = state
        return state

    def load_or_init(self, pipeline_id: str, prd_id: str, feature_id: str, platform: str) -> PipelineState:
        saved = self._store.load_latest(pipeline_id)
        if saved:
            self._cache[pipeline_id] = saved
            return saved
        return self.init_state(pipeline_id, prd_id, feature_id, platform)

    def get(self, pipeline_id: str) -> Optional[PipelineState]:
        return self._cache.get(pipeline_id)

    def save(self, state: PipelineState, description: str = "") -> str:
        self._cache[state.pipeline_id] = state
        return self._store.save(state, description)

    def stage_start(self, state: PipelineState, stage_id: StageID) -> None:
        state.mark_started(stage_id)
        self.save(state, f"Started {stage_id}")

    def stage_complete(self, state: PipelineState, stage_id: StageID, output_ids: list[str]) -> None:
        state.mark_completed(stage_id, output_ids)
        self.save(state, f"Completed {stage_id}")

    def stage_fail(self, state: PipelineState, stage_id: StageID, error: str) -> None:
        state.mark_failed(stage_id, error)
        self.save(state, f"Failed {stage_id}: {error[:80]}")

    def stage_retry(self, state: PipelineState, stage_id: StageID) -> None:
        state.reset_stage_for_retry(stage_id)
        self.save(state, f"Retrying {stage_id}")

    def get_resume_stage(self, state: PipelineState, all_stages: list[StageID]) -> StageID:
        """Return the next stage to run when resuming from a checkpoint."""
        for stage_id in all_stages:
            key = stage_id.value if hasattr(stage_id, "value") else stage_id
            run = state.stages.get(key)
            if run is None or run.status != StageStatus.COMPLETED:
                return stage_id
        return all_stages[-1]
