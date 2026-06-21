"""
Main pipeline runner.
Executes all 24 stages in order, handles the triage loop, checkpointing, and approval gates.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Callable, Optional

import tasks.execution as exec_tasks
import tasks.fs as fs_tasks
import tasks.release as release_tasks
import tasks.scoping as scoping_tasks
import tasks.test_plan as tp_tasks
import tasks.test_scripts as ts_tasks
import tasks.triage as triage_tasks
from models.approvals import ApprovalRequest, ApprovalStatus
from models.artifacts import StageID
from models.pipeline_state import PipelineState, PipelineStatus
from orchestration.approval_manager import ApprovalManager
from orchestration.crew_factory import CrewFactory
from orchestration.prd_ingester import PRDIngester
from orchestration.retry_policy import RetryPolicy
from orchestration.state_manager import StateManager
from storage.artifact_store import ArtifactStore
from telemetry.callbacks import TelemetryCallbacks

logger = logging.getLogger(__name__)


class PipelineRunner:
    # Stages that require a human approval gate (mirrors `human_approval` in pipeline.yaml).
    APPROVAL_STAGES = {
        StageID.TEST_PLAN_REVIEW,
        StageID.FIX,
        StageID.QA_SIGNOFF,
    }
    # Default approver roles per gated stage (used when requesting approval).
    APPROVERS = {
        StageID.TEST_PLAN_REVIEW: ["qa_lead@example.com", "pm@example.com"],
        StageID.FIX: ["dev_lead@example.com", "qa_lead@example.com"],
        StageID.QA_SIGNOFF: ["qa_manager@example.com", "qa_lead@example.com"],
    }

    def __init__(
        self,
        crew_factory: CrewFactory,
        state_manager: StateManager,
        retry_policy: RetryPolicy,
        approval_manager: ApprovalManager,
        artifact_store: ArtifactStore,
        telemetry: TelemetryCallbacks,
        max_triage_loops: int = 5,
        approval_callback: Optional[Callable[[ApprovalRequest], tuple]] = None,
    ):
        self.factory = crew_factory
        self.state_mgr = state_manager
        self.retry = retry_policy
        self.approvals = approval_manager
        self.artifacts = artifact_store
        self.telemetry = telemetry
        self.max_triage_loops = max_triage_loops
        # approval_callback(req) -> (decision, decided_by, comments).
        # Defaults to auto-approve so the pipeline can run unattended (CI / demos).
        self.approval_callback = approval_callback or self._auto_approve

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        prd_id: str,
        feature_id: str,
        platform: str,
        resume_pipeline_id: Optional[str] = None,
        prd_file: Optional[str] = None,
        prd_title: Optional[str] = None,
        feature_title: Optional[str] = None,
    ) -> PipelineState:
        pipeline_id = resume_pipeline_id or f"pipeline_{uuid.uuid4().hex[:8]}"
        state = self.state_mgr.load_or_init(pipeline_id, prd_id, feature_id, platform)

        self.telemetry.on_pipeline_start(state)
        logger.info("Pipeline %s started for feature %s on %s", pipeline_id, feature_id, platform)

        try:
            ctx = {}  # artifact_id context carried through pipeline

            # Stage 0: PRD Ingestion
            prd_id, feature_id = self._ingest_prd(
                prd_id=prd_id,
                feature_id=feature_id,
                prd_file=prd_file,
                prd_title=prd_title,
                feature_title=feature_title,
            )

            ctx = self._run_phase1(state, ctx, prd_id, feature_id)
            ctx = self._run_phase2(state, ctx)
            ctx = self._run_phase3(state, ctx)
            ctx = self._run_phase4(state, ctx)
            ctx = self._run_phase5(state, ctx, pipeline_id)

            state.status = PipelineStatus.COMPLETED
            self.state_mgr.save(state, "Pipeline completed")
            self.telemetry.on_pipeline_complete(state)
            logger.info("Pipeline %s completed successfully", pipeline_id)

        except Exception as exc:
            state.status = PipelineStatus.FAILED
            self.state_mgr.save(state, f"Pipeline failed: {exc}")
            self.telemetry.on_pipeline_fail(state, str(exc))
            logger.error("Pipeline %s failed: %s", pipeline_id, exc)
            raise

        return state

    # ------------------------------------------------------------------
    # Stage 0 — PRD Ingestion
    # ------------------------------------------------------------------

    def _ingest_prd(
        self,
        prd_id: str,
        feature_id: str,
        prd_file: Optional[str],
        prd_title: Optional[str],
        feature_title: Optional[str],
    ) -> tuple[str, str]:
        ingester = PRDIngester(self.artifacts)

        if prd_file:
            logger.info("Ingesting PRD from file: %s", prd_file)
            return ingester.ingest_from_file(
                prd_path=prd_file,
                feature_title=feature_title or prd_id,
                prd_id=prd_id or None,
                feature_id=feature_id or None,
            )

        # Check if both already exist in the store
        existing_prd = self.artifacts.get(prd_id) if prd_id else None
        existing_feat = self.artifacts.get(feature_id) if feature_id else None

        if existing_prd is not None and existing_feat is not None:
            logger.info("PRD and FeatureRequest already in store — skipping ingestion")
            return prd_id, feature_id

        if prd_title and feature_title:
            logger.info("Ingesting PRD from provided title/description")
            return ingester.ingest_from_text(
                prd_title=prd_title,
                prd_description=prd_title,
                requirements=[],
                feature_title=feature_title,
                prd_id=prd_id or None,
                feature_id=feature_id or None,
            )

        raise ValueError(
            "PRD ingestion failed: provide --prd-file, or ensure prd_id/feature_id exist in the store, "
            "or pass prd_title + feature_title."
        )

    # ------------------------------------------------------------------
    # Phase runners
    # ------------------------------------------------------------------

    def _run_phase1(self, state, ctx, prd_id, feature_id) -> dict:
        ctx["prd_id"] = prd_id
        ctx["feature_id"] = feature_id

        ctx["scoping_dev_id"] = self._run_stage(
            state, StageID.SCOPING_DEV,
            lambda: self.factory.dev_scoping_crew(
                scoping_tasks.dev_scoping_task(None, prd_id, feature_id)
            ).kickoff()
        )

        ctx["scoping_qa_id"] = self._run_stage(
            state, StageID.SCOPING_QA,
            lambda: self.factory.qa_scoping_crew(
                scoping_tasks.qa_scoping_task(None, ctx["scoping_dev_id"])
            ).kickoff()
        )

        ctx["fs_id"] = self._run_stage(
            state, StageID.FS_GEN,
            lambda: self.factory.fs_gen_crew(
                fs_tasks.fs_generation_task(None, prd_id, ctx["scoping_dev_id"], ctx["scoping_qa_id"])
            ).kickoff()
        )

        ctx["impl_id"] = self._run_stage(
            state, StageID.DEV_FEATURE_TRACK,
            lambda: self.factory.dev_track_crew(
                fs_tasks.dev_feature_track_task(None, prd_id, ctx["fs_id"])
            ).kickoff()
        )

        return ctx

    def _run_phase2(self, state, ctx) -> dict:
        ctx["fs_review_id"] = self._run_stage(
            state, StageID.FS_REVIEW,
            lambda: self.factory.fs_review_crew(
                fs_tasks.fs_review_task(None, ctx["fs_id"], ctx["prd_id"])
            ).kickoff()
        )

        ctx["test_plan_id"] = self._run_stage(
            state, StageID.TEST_PLAN_GEN,
            lambda: self.factory.test_plan_gen_crew(
                tp_tasks.test_plan_generation_task(
                    None, ctx["fs_id"], ctx.get("topology_id", "default_topology"),
                    impl_summary_id=ctx.get("impl_id"), testing_notes_id=ctx.get("impl_id")
                )
            ).kickoff()
        )

        ctx["approved_plan_id"] = self._run_stage(
            state, StageID.TEST_PLAN_REVIEW,
            lambda: self.factory.test_plan_review_crew(
                tp_tasks.test_plan_review_task(None, ctx["test_plan_id"], ctx["fs_id"])
            ).kickoff()
        )

        return ctx

    def _run_phase3(self, state, ctx) -> dict:
        ctx["scripts_id"] = self._run_stage(
            state, StageID.TEST_SCRIPT_GEN,
            lambda: self.factory.test_script_gen_crew(
                ts_tasks.test_script_generation_task(
                    None, ctx["approved_plan_id"], ctx.get("topology_id", "default_topology"),
                    impl_summary_id=ctx.get("impl_id"), automation_notes_id=ctx.get("impl_id")
                )
            ).kickoff()
        )

        ctx["script_review_id"] = self._run_stage(
            state, StageID.TEST_SCRIPT_REVIEW,
            lambda: self.factory.test_script_review_crew(
                ts_tasks.test_script_review_task(None, ctx["scripts_id"], ctx["approved_plan_id"])
            ).kickoff()
        )

        ctx["coverage_check_id"] = self._run_stage(
            state, StageID.COVERAGE_CHECK,
            lambda: self.factory.coverage_check_crew(
                ts_tasks.coverage_check_task(None, ctx["scripts_id"], ctx["approved_plan_id"])
            ).kickoff()
        )

        return ctx

    def _run_phase4(self, state, ctx) -> dict:
        ctx["stage_result_id"] = self._run_stage(
            state, StageID.STAGE,
            lambda: self.factory.stage_crew(
                exec_tasks.stage_task(None, ctx["scripts_id"], ctx.get("testbed_id", "default_testbed"))
            ).kickoff()
        )

        loop_count = 0
        all_pass = False

        while not all_pass and loop_count < self.max_triage_loops:
            ctx["execution_id"] = self._run_stage(
                state, StageID.EXECUTE,
                lambda: self.factory.execute_crew(
                    exec_tasks.execute_task(None, ctx["stage_result_id"], ctx.get("testbed_id", "default_testbed"))
                ).kickoff()
            )

            ctx["triage_id"] = self._run_stage(
                state, StageID.TRIAGE,
                lambda: self.factory.triage_crew(
                    triage_tasks.triage_task(None, ctx["execution_id"], ctx["scripts_id"])
                ).kickoff()
            )

            triage_result = self.artifacts.get(ctx["triage_id"])
            has_product_bugs = triage_result and triage_result.get("product_bugs")

            if not has_product_bugs:
                all_pass = True
                logger.info("Triage loop %d complete — no product bugs, exiting loop", loop_count + 1)
                break

            ctx["bug_ids"] = self._run_stage(
                state, StageID.BUG_FILE,
                lambda: self.factory.bug_file_crew(
                    triage_tasks.bug_file_task(None, ctx["triage_id"])
                ).kickoff()
            )

            ctx["repro_id"] = self._run_stage(
                state, StageID.BUG_REPRO,
                lambda: self.factory.bug_repro_crew(
                    triage_tasks.bug_repro_task(None, ctx["bug_ids"], ctx["scripts_id"], ctx.get("testbed_id", "default_testbed"))
                ).kickoff()
            )

            ctx["patch_id"] = self._run_stage(
                state, StageID.FIX,
                lambda: self.factory.fix_crew(
                    triage_tasks.fix_task(None, ctx["bug_ids"], ctx["repro_id"], ctx["scripts_id"])
                ).kickoff()
            )

            ctx["fix_verify_id"] = self._run_stage(
                state, StageID.FIX_VERIFY,
                lambda: self.factory.fix_verify_crew(
                    triage_tasks.fix_verify_task(None, ctx["patch_id"], ctx["execution_id"])
                ).kickoff()
            )

            loop_count += 1
            state.triage_loop_count = loop_count
            self.state_mgr.save(state, f"Triage loop {loop_count} complete")

        return ctx

    def _run_phase5(self, state, ctx, pipeline_id) -> dict:
        ctx["kt_id"] = self._run_stage(
            state, StageID.SUPPORT_KT,
            lambda: self.factory.support_kt_crew(
                release_tasks.support_kt_task(None, ctx.get("fix_verify_id", ""), ctx["approved_plan_id"], ctx["execution_id"])
            ).kickoff()
        )

        ctx["docs_id"] = self._run_stage(
            state, StageID.DOCS_GEN,
            lambda: self.factory.docs_crew(
                release_tasks.docs_task(None, ctx["fs_id"], ctx["approved_plan_id"], ctx["execution_id"])
            ).kickoff()
        )

        ctx["coverage_final_id"] = self._run_stage(
            state, StageID.COVERAGE_FINAL,
            lambda: self.factory.coverage_final_crew(
                release_tasks.coverage_final_task(None, ctx["execution_id"], ctx["approved_plan_id"], ctx["coverage_check_id"])
            ).kickoff()
        )

        ctx["sit_id"] = self._run_stage(
            state, StageID.SIT,
            lambda: self.factory.sit_crew(
                release_tasks.sit_task(None, ctx["scripts_id"], ctx["execution_id"])
            ).kickoff()
        )

        ctx["nightly_profile_id"] = self._run_stage(
            state, StageID.NIGHTLY_INTEGRATION,
            lambda: self.factory.nightly_integration_crew(
                release_tasks.nightly_integration_task(None, ctx["scripts_id"], ctx["sit_id"])
            ).kickoff()
        )

        ctx["nightly_report_id"] = self._run_stage(
            state, StageID.NIGHTLY_REPORTING,
            lambda: self.factory.nightly_reporting_crew(
                release_tasks.nightly_reporting_task(None, ctx["nightly_profile_id"], ctx["execution_id"])
            ).kickoff()
        )

        ctx["signoff_id"] = self._run_stage(
            state, StageID.QA_SIGNOFF,
            lambda: self.factory.qa_signoff_crew(
                release_tasks.qa_signoff_task(
                    None, ctx["kt_id"], ctx["docs_id"], ctx["coverage_final_id"],
                    ctx["sit_id"], ctx["nightly_report_id"]
                )
            ).kickoff()
        )

        ctx["feedback_id"] = self._run_stage(
            state, StageID.FEEDBACK,
            lambda: self.factory.feedback_crew(
                release_tasks.feedback_task(None, pipeline_id)
            ).kickoff()
        )

        return ctx

    # ------------------------------------------------------------------
    # Stage execution helper
    # ------------------------------------------------------------------

    def _run_stage(self, state: PipelineState, stage_id: StageID, fn) -> str:
        stage_key = stage_id.value if hasattr(stage_id, "value") else stage_id
        stage_run = state.stages.get(stage_key)
        if stage_run and stage_run.status == "completed":
            logger.info("Stage %s already completed, skipping", stage_id)
            return stage_run.output_artifact_ids[0] if stage_run.output_artifact_ids else ""

        self.state_mgr.stage_start(state, stage_id)
        self.telemetry.on_stage_start(state.pipeline_id, stage_id)

        def _exec():
            result = fn()
            # Persist the stage output as a first-class artifact so downstream
            # stages can resolve it by ID via the ArtifactStore.
            artifact_id = self._persist_artifact(stage_key, result)
            self.state_mgr.stage_complete(state, stage_id, [artifact_id])
            self.telemetry.on_stage_complete(state.pipeline_id, stage_id)
            # Enforce the human approval gate (if any) after the artifact exists.
            if stage_id in self.APPROVAL_STAGES:
                self._handle_approval(state, stage_id, artifact_id)
            return artifact_id

        def _on_retry(attempt, exc):
            self.state_mgr.stage_retry(state, stage_id)
            self.telemetry.on_stage_retry(state.pipeline_id, stage_id, attempt, str(exc))

        return self.retry.execute(_exec, stage_id, on_retry=_on_retry)

    # ------------------------------------------------------------------
    # Artifact persistence
    # ------------------------------------------------------------------

    def _persist_artifact(self, stage_key: str, result) -> str:
        """Store a stage's crew output in the ArtifactStore and return its ID."""
        artifact_id = f"{stage_key}_{uuid.uuid4().hex[:8]}"
        raw = str(result).strip() if result is not None else ""

        # Prefer structured JSON output; fall back to wrapping raw text.
        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                data = {"value": data}
        except (json.JSONDecodeError, ValueError):
            data = {"raw": raw}

        self.artifacts.store(artifact_id, stage_key, stage_key, data)
        return artifact_id

    # ------------------------------------------------------------------
    # Human-in-the-loop approval gates
    # ------------------------------------------------------------------

    def _handle_approval(self, state: PipelineState, stage_id: StageID, artifact_id: str) -> None:
        approvers = self.APPROVERS.get(stage_id, ["approver@example.com"])
        req = self.approvals.request(
            pipeline_id=state.pipeline_id,
            stage_id=stage_id,
            requester="orchestrator",
            approvers=approvers,
            context={"stage": stage_id.value if hasattr(stage_id, "value") else stage_id},
            artifact_ids=[artifact_id],
            minimum_approvals=1,
        )

        state.status = PipelineStatus.AWAITING_APPROVAL
        self.state_mgr.save(state, f"Awaiting approval for {stage_id}")

        decision, decided_by, comments = self.approval_callback(req)
        self.approvals.decide(req.approval_id, decided_by, decision, comments)
        status = self.approvals.get_status(req.approval_id)

        if status != ApprovalStatus.APPROVED:
            raise RuntimeError(
                f"Approval gate for stage '{stage_id}' was not approved (status={status})."
            )

        state.status = PipelineStatus.IN_PROGRESS
        self.state_mgr.save(state, f"Approved {stage_id} by {decided_by}")
        logger.info("Approval gate %s passed (by %s)", stage_id, decided_by)

    @staticmethod
    def _auto_approve(req: ApprovalRequest) -> tuple:
        """Default non-interactive approver: approves using the first listed approver."""
        approver = req.approvers[0] if req.approvers else "approver@example.com"
        return "approved", approver, "Auto-approved (non-interactive mode)"
