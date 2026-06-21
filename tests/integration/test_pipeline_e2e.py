"""
End-to-end pipeline integration tests.

These exercise the *real* orchestration logic (phase sequencing, the triage
loop, checkpointing, artifact persistence, and human-approval gates) using a
fake crew factory — so they are fully deterministic and require no LLM,
Ollama, or CrewAI install.
"""

import json

import pytest
import tasks.execution as execution_tasks
import tasks.fs as fs_tasks
import tasks.release as release_tasks
import tasks.scoping as scoping_tasks
import tasks.test_plan as test_plan_tasks
import tasks.test_scripts as test_scripts_tasks
import tasks.triage as triage_tasks
from models.artifacts import StageID
from models.pipeline_state import PipelineStatus, StageStatus
from orchestration.approval_manager import ApprovalManager
from orchestration.pipeline_runner import PipelineRunner
from orchestration.retry_policy import RetryPolicy
from orchestration.state_manager import StateManager
from storage.artifact_store import ArtifactStore
from storage.checkpoint_store import CheckpointStore
from telemetry.callbacks import TelemetryCallbacks
from telemetry.metrics import MetricsCollector

TASK_MODULES = [
    scoping_tasks,
    fs_tasks,
    test_plan_tasks,
    test_scripts_tasks,
    execution_tasks,
    triage_tasks,
    release_tasks,
]


class _FakeCrew:
    def __init__(self, output):
        self._output = output

    def kickoff(self):
        return self._output


class FakeCrewFactory:
    """Duck-typed stand-in for CrewFactory: every ``*_crew(task)`` returns a fake crew."""

    def __init__(self, outputs=None, default='{"status": "ok"}'):
        self.outputs = outputs or {}
        self.default = default
        self.calls = []

    def __getattr__(self, name):
        def _make(task=None, *args, **kwargs):
            self.calls.append(name)
            out = self.outputs.get(name, self.default)
            if callable(out):
                out = out()
            return _FakeCrew(out)

        return _make


@pytest.fixture
def stub_tasks(monkeypatch):
    """Replace every ``*_task`` factory with a no-op (the fake crew ignores tasks)."""
    for module in TASK_MODULES:
        for attr in list(vars(module)):
            if attr.endswith("_task") and callable(getattr(module, attr)):
                monkeypatch.setattr(module, attr, lambda *a, **k: None)


def _build_runner(tmp_path, factory, approval_callback=None):
    artifacts = ArtifactStore(db_path=str(tmp_path / "artifacts.db"))
    checkpoints = CheckpointStore(db_path=str(tmp_path / "checkpoints.db"))
    return PipelineRunner(
        crew_factory=factory,
        state_manager=StateManager(checkpoint_store=checkpoints),
        retry_policy=RetryPolicy(max_retries=0),
        approval_manager=ApprovalManager(),
        artifact_store=artifacts,
        telemetry=TelemetryCallbacks(metrics_collector=MetricsCollector()),
        max_triage_loops=5,
        approval_callback=approval_callback,
    ), artifacts


def _run(runner, platform="CLOUD"):
    return runner.run(
        prd_id="",
        feature_id="",
        platform=platform,
        prd_title="Sample Feature",
        feature_title="Sample feature for E2E test",
    )


# ----------------------------------------------------------------------
# Happy path
# ----------------------------------------------------------------------


def test_full_pipeline_completes(tmp_path, stub_tasks):
    factory = FakeCrewFactory()
    runner, artifacts = _build_runner(tmp_path, factory)

    state = _run(runner)

    # Pipeline reaches COMPLETED.
    assert state.status == PipelineStatus.COMPLETED

    # No product bugs => triage loop exits after one pass, so bug stages are skipped.
    completed = {sid for sid, run in state.stages.items() if run.status == StageStatus.COMPLETED}
    expected = {
        "scoping_dev",
        "scoping_qa",
        "fs_gen",
        "dev_feature_track",
        "fs_review",
        "test_plan_gen",
        "test_plan_review",
        "test_script_gen",
        "test_script_review",
        "coverage_check",
        "stage",
        "execute",
        "triage",
        "support_kt",
        "docs_gen",
        "coverage_final",
        "sit",
        "nightly_integration",
        "nightly_reporting",
        "qa_signoff",
        "feedback",
    }
    assert expected <= completed
    # Bug stages should NOT have run.
    assert "fix" not in completed
    assert "bug_file" not in completed


def test_stage_outputs_are_persisted(tmp_path, stub_tasks):
    factory = FakeCrewFactory()
    runner, artifacts = _build_runner(tmp_path, factory)

    state = _run(runner)

    # Every completed stage has a resolvable artifact in the store.
    for sid, run in state.stages.items():
        assert run.output_artifact_ids, f"{sid} has no output artifact"
        artifact_id = run.output_artifact_ids[0]
        assert artifacts.get(artifact_id) is not None, f"artifact for {sid} not persisted"


# ----------------------------------------------------------------------
# Human-in-the-loop approval gates
# ----------------------------------------------------------------------


def test_approval_gates_are_invoked(tmp_path, stub_tasks):
    seen = []

    def record_and_approve(req):
        seen.append(req.stage_id)
        return "approved", req.approvers[0], "ok"

    factory = FakeCrewFactory()
    runner, _ = _build_runner(tmp_path, factory, approval_callback=record_and_approve)

    state = _run(runner)

    assert state.status == PipelineStatus.COMPLETED
    # Gated stages reached on the happy path: test_plan_review and qa_signoff.
    assert StageID.TEST_PLAN_REVIEW.value in seen
    assert StageID.QA_SIGNOFF.value in seen


def test_rejected_approval_fails_pipeline(tmp_path, stub_tasks):
    def reject(req):
        return "rejected", req.approvers[0], "not acceptable"

    factory = FakeCrewFactory()
    runner, _ = _build_runner(tmp_path, factory, approval_callback=reject)

    with pytest.raises(RuntimeError, match="not approved"):
        _run(runner)

    state = runner.state_mgr.get(next(iter(runner.state_mgr._cache)))
    assert state.status == PipelineStatus.FAILED


# ----------------------------------------------------------------------
# Triage loop
# ----------------------------------------------------------------------


def test_triage_loop_runs_bug_stages_when_bugs_found(tmp_path, stub_tasks):
    # Triage reports a product bug on the first pass, then a clean pass.
    triage_outputs = iter(
        [
            json.dumps({"product_bugs": ["TC-001"]}),
            json.dumps({"product_bugs": []}),
        ]
    )

    factory = FakeCrewFactory(outputs={"triage_crew": lambda: next(triage_outputs)})
    runner, _ = _build_runner(tmp_path, factory)

    state = _run(runner)

    assert state.status == PipelineStatus.COMPLETED
    completed = {sid for sid, run in state.stages.items() if run.status == StageStatus.COMPLETED}
    # The bug-handling stages must have executed because a product bug was found.
    assert {"bug_file", "bug_repro", "fix", "fix_verify"} <= completed
    assert state.triage_loop_count >= 1
