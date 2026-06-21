"""Unit tests for artifact and state models."""

from models.approvals import ApprovalRequest, ApprovalStatus
from models.artifacts import ArtifactMeta, Ownership, ScopingDecision, StageID
from models.pipeline_state import PipelineState, PipelineStatus, StageStatus


class TestArtifactMeta:
    def test_default_id_generated(self):
        meta = ArtifactMeta(
            stage_id=StageID.SCOPING_DEV, ownership=Ownership.DEV, created_by="agent"
        )
        assert meta.artifact_id is not None
        assert len(meta.artifact_id) > 0

    def test_version_defaults_to_one(self):
        meta = ArtifactMeta(stage_id=StageID.FS_GEN, ownership=Ownership.DEV, created_by="agent")
        assert meta.version == 1

    def test_mandatory_defaults_true(self):
        meta = ArtifactMeta(stage_id=StageID.FS_GEN, ownership=Ownership.DEV, created_by="agent")
        assert meta.is_mandatory is True


class TestScopingDecision:
    def test_valid_scoping_decision(self):
        decision = ScopingDecision(
            decision="in-scope",
            rationale="Feature is feasible within current sprint",
            feature_short_name="bgp_gr",
            technology_classification={"protocol": "BGP", "platform": "CLOUD"},
            scope_boundaries=["single-VRF only"],
        )
        assert decision.decision == "in-scope"
        assert "bgp_gr" == decision.feature_short_name


class TestPipelineState:
    def _make_state(self) -> PipelineState:
        return PipelineState(
            pipeline_id="pipe_001", prd_id="prd_001", feature_id="feat_001", platform="CLOUD"
        )

    def test_initial_status(self):
        state = self._make_state()
        assert state.status == PipelineStatus.NOT_STARTED

    def test_mark_started(self):
        state = self._make_state()
        state.mark_started(StageID.SCOPING_DEV)
        assert state.status == PipelineStatus.IN_PROGRESS
        run = state.get_stage(StageID.SCOPING_DEV)
        assert run.status == StageStatus.IN_PROGRESS

    def test_mark_completed(self):
        state = self._make_state()
        state.mark_started(StageID.SCOPING_DEV)
        state.mark_completed(StageID.SCOPING_DEV, ["artifact_123"])
        run = state.get_stage(StageID.SCOPING_DEV)
        assert run.status == StageStatus.COMPLETED
        assert "artifact_123" in run.output_artifact_ids
        assert run.duration_seconds is not None

    def test_mark_failed(self):
        state = self._make_state()
        state.mark_started(StageID.SCOPING_DEV)
        state.mark_failed(StageID.SCOPING_DEV, "LLM rate limit exceeded")
        assert state.status == PipelineStatus.FAILED
        run = state.get_stage(StageID.SCOPING_DEV)
        assert run.status == StageStatus.FAILED
        assert "rate limit" in run.error

    def test_reset_for_retry(self):
        state = self._make_state()
        state.mark_started(StageID.SCOPING_DEV)
        state.mark_failed(StageID.SCOPING_DEV, "timeout")
        state.reset_stage_for_retry(StageID.SCOPING_DEV)
        run = state.get_stage(StageID.SCOPING_DEV)
        assert run.status == StageStatus.PENDING
        assert run.retry_count == 1

    def test_summary(self):
        state = self._make_state()
        state.mark_started(StageID.SCOPING_DEV)
        state.mark_completed(StageID.SCOPING_DEV, [])
        s = state.summary()
        assert s["completed_stages"] == 1
        assert s["failed_stages"] == 0


class TestApprovalRequest:
    def _make_request(self) -> ApprovalRequest:
        return ApprovalRequest(
            pipeline_id="pipe_001",
            stage_id=StageID.TEST_PLAN_REVIEW,
            requester="qa_agent",
            approvers=["qa_lead@example.com", "pm@example.com"],
            minimum_approvals=2,
            context={"plan_id": "plan_001"},
        )

    def test_initial_status_pending(self):
        req = self._make_request()
        assert req.status == ApprovalStatus.PENDING

    def test_not_approved_without_decisions(self):
        req = self._make_request()
        assert not req.is_approved()

    def test_pending_approvers(self):
        req = self._make_request()
        pending = req.pending_approvers()
        assert "qa_lead@example.com" in pending
        assert "pm@example.com" in pending
