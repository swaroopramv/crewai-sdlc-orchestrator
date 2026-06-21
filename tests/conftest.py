"""Shared pytest fixtures for unit and integration tests."""


import pytest
from models.pipeline_state import PipelineState
from orchestration.approval_manager import ApprovalManager
from orchestration.prd_ingester import PRDIngester
from orchestration.retry_policy import RetryPolicy
from orchestration.state_manager import StateManager
from storage.artifact_store import ArtifactStore
from storage.checkpoint_store import CheckpointStore

# ------------------------------------------------------------------
# Storage
# ------------------------------------------------------------------

@pytest.fixture
def artifact_store(tmp_path):
    return ArtifactStore(db_path=str(tmp_path / "artifacts.db"))


@pytest.fixture
def checkpoint_store(tmp_path):
    return CheckpointStore(db_path=str(tmp_path / "checkpoints.db"))


# ------------------------------------------------------------------
# Orchestration components
# ------------------------------------------------------------------

@pytest.fixture
def approval_manager():
    return ApprovalManager(default_timeout_hours=1)


@pytest.fixture
def state_manager(checkpoint_store):
    return StateManager(checkpoint_store=checkpoint_store)


@pytest.fixture
def retry_policy():
    return RetryPolicy(max_retries=2, base_delay_seconds=0, backoff_multiplier=1.0)


@pytest.fixture
def prd_ingester(artifact_store):
    return PRDIngester(artifact_store)


# ------------------------------------------------------------------
# Pre-built pipeline state
# ------------------------------------------------------------------

@pytest.fixture
def pipeline_state():
    return PipelineState(
        pipeline_id="pipe_test_001",
        prd_id="prd_001",
        feature_id="feat_001",
        platform="CLOUD",
    )


@pytest.fixture
def pipeline_state_with_prd(artifact_store):
    """Pipeline state where PRD and FeatureRequest are already in the store."""
    artifact_store.store("prd_001", "prd_ingestion", "PRD", {
        "prd_id": "prd_001",
        "title": "BGP Graceful Restart",
        "description": "Support GR per RFC 4724",
        "requirements": [{"id": "REQ-001", "description": "Must support RFC 4724", "priority": "must"}],
    })
    artifact_store.store("feat_001", "prd_ingestion", "FeatureRequest", {
        "request_id": "feat_001",
        "title": "BGP GR Support",
        "description": "Implement BGP Graceful Restart",
        "priority": "high",
    })
    return PipelineState(
        pipeline_id="pipe_test_002",
        prd_id="prd_001",
        feature_id="feat_001",
        platform="CLOUD",
    )


# ------------------------------------------------------------------
# Sample artifacts
# ------------------------------------------------------------------

@pytest.fixture
def sample_prd_data():
    return {
        "prd_id": "prd_001",
        "title": "BGP Graceful Restart",
        "description": "Feature description",
        "requirements": [
            {"id": "REQ-001", "description": "Must support RFC 4724", "priority": "must"},
            {"id": "REQ-002", "description": "Must not cause session reset", "priority": "must"},
        ],
    }


@pytest.fixture
def sample_scoping_decision():
    return {
        "decision_id": "scope_001",
        "decision": "in-scope",
        "rationale": "Feasible in current sprint",
        "feature_short_name": "bgp_gr",
        "technology_classification": {"protocol": "BGP", "platform": "CLOUD"},
        "scope_boundaries": ["Single VRF only"],
    }


@pytest.fixture
def sample_test_plan():
    return {
        "plan_id": "plan_001",
        "fs_id": "fs_001",
        "test_scenarios": [
            {"id": "TC-001", "name": "Basic GR negotiation", "type": "positive", "fs_req_id": "REQ-001"},
            {"id": "TC-002", "name": "GR timeout handling", "type": "negative", "fs_req_id": "REQ-002"},
        ],
        "expected_results": [
            {"tc_id": "TC-001", "expected": "GR capability negotiated successfully"},
            {"tc_id": "TC-002", "expected": "Session maintained after timeout"},
        ],
        "coverage_mapping": {"REQ-001": ["TC-001"], "REQ-002": ["TC-002"]},
        "approved": True,
    }


@pytest.fixture
def sample_execution_result():
    return {
        "execution_id": "exec_001",
        "testbed_id": "testbed_cloud_001",
        "pass_count": 18,
        "fail_count": 2,
        "total_count": 20,
        "pass_rate": 90.0,
        "logs": ["FAILED TC-015: AssertionError", "FAILED TC-018: TimeoutError"],
        "ci_ref": "ci://job/12345",
    }


@pytest.fixture
def sample_triage_report():
    return {
        "triage_id": "triage_001",
        "execution_id": "exec_001",
        "failure_classifications": [
            {"tc_id": "TC-015", "type": "PRODUCT_BUG", "summary": "Null pointer in GR handler"},
            {"tc_id": "TC-018", "type": "TEST_ISSUE", "summary": "Incorrect timeout value in script"},
        ],
        "root_cause_analysis": ["GR handler does not check for null peer state"],
        "product_bugs": ["TC-015"],
        "test_issues": ["TC-018"],
    }


# ------------------------------------------------------------------
# Sample PRD files
# ------------------------------------------------------------------

@pytest.fixture
def prd_markdown_file(tmp_path):
    content = (
        "# BGP Graceful Restart\n\n"
        "This feature implements BGP Graceful Restart per RFC 4724.\n\n"
        "## Requirements\n\n"
        "- Must support all address families\n"
        "- Must not cause BGP session reset\n"
        "- Should support stale routes for up to 300 seconds\n"
        "- Must interoperate with existing BGP implementations\n"
    )
    p = tmp_path / "prd_bgp_gr.md"
    p.write_text(content)
    return str(p)


@pytest.fixture
def prd_json_file(tmp_path, sample_prd_data):
    import json
    p = tmp_path / "prd.json"
    p.write_text(json.dumps(sample_prd_data))
    return str(p)
