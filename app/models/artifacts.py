"""Pydantic models for all SDLC artifacts."""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class StageID(str, Enum):
    PRD_INGESTION = "prd_ingestion"
    SCOPING_DEV = "scoping_dev"
    SCOPING_QA = "scoping_qa"
    FS_GEN = "fs_gen"
    DEV_FEATURE_TRACK = "dev_feature_track"
    FS_REVIEW = "fs_review"
    TEST_PLAN_GEN = "test_plan_gen"
    TEST_PLAN_REVIEW = "test_plan_review"
    TEST_SCRIPT_GEN = "test_script_gen"
    TEST_SCRIPT_REVIEW = "test_script_review"
    COVERAGE_CHECK = "coverage_check"
    STAGE = "stage"
    EXECUTE = "execute"
    TRIAGE = "triage"
    BUG_FILE = "bug_file"
    BUG_REPRO = "bug_repro"
    FIX = "fix"
    FIX_VERIFY = "fix_verify"
    SUPPORT_KT = "support_kt"
    DOCS_GEN = "docs_gen"
    COVERAGE_FINAL = "coverage_final"
    SIT = "sit"
    NIGHTLY_INTEGRATION = "nightly_integration"
    NIGHTLY_REPORTING = "nightly_reporting"
    QA_SIGNOFF = "qa_signoff"
    FEEDBACK = "feedback"


class Ownership(str, Enum):
    DEV = "DEV"
    QA = "QA"
    CO_OWNED = "CO_OWNED"
    ORCHESTRATOR = "ORCHESTRATOR"


class ArtifactMeta(BaseModel):
    artifact_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    stage_id: StageID
    ownership: Ownership
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    version: int = 1
    parent_ids: List[str] = Field(default_factory=list)
    is_mandatory: bool = True

    class Config:
        use_enum_values = True


class PRD(BaseModel):
    prd_id: str
    title: str
    description: str
    requirements: List[Dict[str, Any]] = Field(default_factory=list)
    feature_id: Optional[str] = None
    meta: Optional[ArtifactMeta] = None


class FeatureRequest(BaseModel):
    request_id: str
    title: str
    description: str
    priority: str = "medium"
    requestor: Optional[str] = None
    meta: Optional[ArtifactMeta] = None


class ScopingDecision(BaseModel):
    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    decision: str  # in-scope / out-of-scope / partial
    rationale: str
    feature_short_name: str
    technology_classification: Dict[str, str] = Field(default_factory=dict)
    scope_boundaries: List[str] = Field(default_factory=list)
    meta: Optional[ArtifactMeta] = None


class TestConsiderations(BaseModel):
    considerations_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    testability_assessment: str
    coverage_scope: List[str] = Field(default_factory=list)
    automation_feasibility: str
    topology_requirements: List[str] = Field(default_factory=list)
    updated_scoping_decision: Optional[ScopingDecision] = None
    meta: Optional[ArtifactMeta] = None


class FS(BaseModel):
    fs_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    feature_description: str
    functional_requirements: List[Dict[str, Any]] = Field(default_factory=list)
    non_functional_requirements: List[Dict[str, Any]] = Field(default_factory=list)
    traceability_matrix: Dict[str, Any] = Field(default_factory=dict)
    meta: Optional[ArtifactMeta] = None


class ImplArtifacts(BaseModel):
    impl_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    impl_plan: str
    impl_summary: str
    testing_notes: str
    automation_notes: str
    trace_log: Optional[str] = None
    meta: Optional[ArtifactMeta] = None


class SFSReviewReport(BaseModel):
    review_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    fs_id: str
    completeness_score: float = Field(ge=0, le=10)
    correctness_score: float = Field(ge=0, le=10)
    test_readiness_gaps: List[str] = Field(default_factory=list)
    review_comments: List[str] = Field(default_factory=list)
    approved: bool = False
    meta: Optional[ArtifactMeta] = None


class TestPlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    fs_id: str
    test_scenarios: List[Dict[str, Any]] = Field(default_factory=list)
    expected_results: List[Dict[str, Any]] = Field(default_factory=list)
    coverage_mapping: Dict[str, Any] = Field(default_factory=dict)
    topology_requirements: List[str] = Field(default_factory=list)
    approved: bool = False
    meta: Optional[ArtifactMeta] = None


class TestScripts(BaseModel):
    scripts_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    plan_id: str
    script_paths: List[str] = Field(default_factory=list)
    libraries: List[str] = Field(default_factory=list)
    test_data: Dict[str, Any] = Field(default_factory=dict)
    project_structure: Dict[str, Any] = Field(default_factory=dict)
    meta: Optional[ArtifactMeta] = None


class CTCResult(BaseModel):
    coverage_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    plan_id: str
    coverage_percentage: float = Field(ge=0, le=100)
    coverage_gaps: List[str] = Field(default_factory=list)
    scenario_coverage: Dict[str, bool] = Field(default_factory=dict)
    meta: Optional[ArtifactMeta] = None


class ExecutionResult(BaseModel):
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    testbed_id: str
    pass_count: int = 0
    fail_count: int = 0
    total_count: int = 0
    pass_rate: float = 0.0
    logs: List[str] = Field(default_factory=list)
    duration_seconds: Optional[float] = None
    ci_ref: Optional[str] = None
    meta: Optional[ArtifactMeta] = None

    def compute_pass_rate(self):
        if self.total_count > 0:
            self.pass_rate = (self.pass_count / self.total_count) * 100


class TriageReport(BaseModel):
    triage_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    execution_id: str
    failure_classifications: List[Dict[str, Any]] = Field(default_factory=list)
    root_cause_analysis: List[str] = Field(default_factory=list)
    product_bugs: List[str] = Field(default_factory=list)
    test_issues: List[str] = Field(default_factory=list)
    meta: Optional[ArtifactMeta] = None


class BugRecord(BaseModel):
    bug_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    issue_tracker_id: Optional[str] = None
    triage_id: str
    title: str
    description: str
    severity: str
    priority: str
    reproduction_steps: List[str] = Field(default_factory=list)
    status: str = "open"
    meta: Optional[ArtifactMeta] = None


class ReproResult(BaseModel):
    repro_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    bug_id: str
    reproduced: bool
    reproduction_steps: List[str] = Field(default_factory=list)
    environment_details: Dict[str, Any] = Field(default_factory=dict)
    meta: Optional[ArtifactMeta] = None


class FixPatch(BaseModel):
    patch_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    bug_id: str
    description: str
    code_changes: Dict[str, Any] = Field(default_factory=dict)
    updated_script_ids: List[str] = Field(default_factory=list)
    meta: Optional[ArtifactMeta] = None


class R2VResult(BaseModel):
    fix_verify_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patch_id: str
    validation_passed: bool = False
    regression_detected: bool = False
    validation_summary: str = ""
    meta: Optional[ArtifactMeta] = None


class TACTOIDoc(BaseModel):
    kt_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    feature_id: str
    content: str
    support_notes: List[str] = Field(default_factory=list)
    meta: Optional[ArtifactMeta] = None


class FeatureDocs(BaseModel):
    doc_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    feature_id: str
    content: str
    release_notes: Optional[str] = None
    meta: Optional[ArtifactMeta] = None


class DTESignoff(BaseModel):
    signoff_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    feature_id: str
    status: str = "pending"
    qa_artifacts: Dict[str, Any] = Field(default_factory=dict)
    fcs_artifacts: Dict[str, Any] = Field(default_factory=dict)
    signoff_comments: List[str] = Field(default_factory=list)
    signed_by: Optional[str] = None
    signed_at: Optional[datetime] = None
    meta: Optional[ArtifactMeta] = None


class FeedbackReport(BaseModel):
    feedback_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pipeline_id: str
    overall_rating: float = Field(ge=0, le=10)
    stage_feedback: Dict[str, str] = Field(default_factory=dict)
    suggestions: List[str] = Field(default_factory=list)
    meta: Optional[ArtifactMeta] = None
