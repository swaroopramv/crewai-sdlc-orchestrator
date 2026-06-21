"""Unit tests for artifact store and checkpoint store."""

import pytest
from models.pipeline_state import PipelineState
from storage.artifact_store import ArtifactStore
from storage.checkpoint_store import CheckpointStore


@pytest.fixture
def artifact_store(tmp_path):
    return ArtifactStore(db_path=str(tmp_path / "test_artifacts.db"))


@pytest.fixture
def checkpoint_store(tmp_path):
    return CheckpointStore(db_path=str(tmp_path / "test_checkpoints.db"))


@pytest.fixture
def sample_state():
    return PipelineState(
        pipeline_id="pipe_test_001", prd_id="prd_001", feature_id="feat_001", platform="CLOUD"
    )


class TestArtifactStore:
    def test_store_and_retrieve(self, artifact_store):
        data = {"decision": "in-scope", "feature_short_name": "bgp_gr"}
        artifact_store.store("art_001", "scoping_dev", "ScopingDecision", data)
        result = artifact_store.get("art_001")
        assert result["decision"] == "in-scope"
        assert result["feature_short_name"] == "bgp_gr"

    def test_get_missing_returns_none(self, artifact_store):
        assert artifact_store.get("nonexistent") is None

    def test_list_by_stage(self, artifact_store):
        artifact_store.store("art_001", "scoping_dev", "ScopingDecision", {"x": 1})
        artifact_store.store("art_002", "scoping_dev", "ScopingDecision", {"x": 2})
        artifact_store.store("art_003", "fs_gen", "FS", {"title": "test"})

        results = artifact_store.list_by_stage("scoping_dev")
        assert len(results) == 2
        ids = {r["artifact_id"] for r in results}
        assert "art_001" in ids
        assert "art_002" in ids

    def test_overwrite_existing(self, artifact_store):
        artifact_store.store("art_001", "scoping_dev", "ScopingDecision", {"v": 1})
        artifact_store.store("art_001", "scoping_dev", "ScopingDecision", {"v": 2})
        result = artifact_store.get("art_001")
        assert result["v"] == 2

    def test_delete(self, artifact_store):
        artifact_store.store("art_001", "scoping_dev", "ScopingDecision", {})
        deleted = artifact_store.delete("art_001")
        assert deleted is True
        assert artifact_store.get("art_001") is None

    def test_delete_missing_returns_false(self, artifact_store):
        assert artifact_store.delete("nonexistent") is False


class TestCheckpointStore:
    def test_save_and_load_latest(self, checkpoint_store, sample_state):
        checkpoint_store.save(sample_state, "Initial checkpoint")
        loaded = checkpoint_store.load_latest(sample_state.pipeline_id)
        assert loaded is not None
        assert loaded.pipeline_id == sample_state.pipeline_id
        assert loaded.prd_id == sample_state.prd_id

    def test_load_latest_returns_none_for_unknown(self, checkpoint_store):
        assert checkpoint_store.load_latest("unknown_pipeline") is None

    def test_list_checkpoints(self, checkpoint_store, sample_state):
        checkpoint_store.save(sample_state, "cp1")
        checkpoint_store.save(sample_state, "cp2")
        cps = checkpoint_store.list_checkpoints(sample_state.pipeline_id)
        assert len(cps) == 2

    def test_delete_old_keeps_latest(self, checkpoint_store, sample_state):
        for i in range(7):
            checkpoint_store.save(sample_state, f"cp_{i}")
        deleted = checkpoint_store.delete_old(sample_state.pipeline_id, keep=5)
        assert deleted == 2
        remaining = checkpoint_store.list_checkpoints(sample_state.pipeline_id)
        assert len(remaining) == 5

    def test_cleanup(self, checkpoint_store, sample_state):
        checkpoint_store.save(sample_state, "cp")
        removed = checkpoint_store.cleanup(sample_state.pipeline_id)
        assert removed >= 1
        assert checkpoint_store.load_latest(sample_state.pipeline_id) is None
