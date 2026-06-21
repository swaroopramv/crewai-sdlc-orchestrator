"""Unit tests for PRD ingester (Stage 0)."""

import json
import pytest
from pathlib import Path

from storage.artifact_store import ArtifactStore
from orchestration.prd_ingester import PRDIngester


@pytest.fixture
def store(tmp_path):
    return ArtifactStore(db_path=str(tmp_path / "test.db"))


@pytest.fixture
def ingester(store):
    return PRDIngester(store)


class TestPRDIngesterFromText:
    def test_ingest_stores_prd_and_feature(self, ingester, store):
        prd_id, feat_id = ingester.ingest_from_text(
            prd_title="BGP Graceful Restart",
            prd_description="Support BGP GR on CLOUD platforms",
            requirements=[{"id": "REQ-001", "description": "Must support RFC 4724", "priority": "must"}],
            feature_title="BGP Graceful Restart Support",
        )
        assert store.get(prd_id) is not None
        assert store.get(feat_id) is not None

    def test_prd_has_correct_title(self, ingester, store):
        prd_id, _ = ingester.ingest_from_text(
            prd_title="OSPF Fast Convergence",
            prd_description="Reduce OSPF convergence time",
            requirements=[],
            feature_title="OSPF Fast Convergence",
        )
        data = store.get(prd_id)
        assert data["title"] == "OSPF Fast Convergence"

    def test_requirements_stored(self, ingester, store):
        reqs = [
            {"id": "REQ-001", "description": "Must reduce failover time to < 1s", "priority": "must"},
            {"id": "REQ-002", "description": "Should support all VRFs", "priority": "should"},
        ]
        prd_id, _ = ingester.ingest_from_text(
            prd_title="Fast Failover",
            prd_description="...",
            requirements=reqs,
            feature_title="Fast Failover",
        )
        data = store.get(prd_id)
        assert len(data["requirements"]) == 2

    def test_custom_ids_respected(self, ingester, store):
        prd_id, feat_id = ingester.ingest_from_text(
            prd_title="T",
            prd_description="D",
            requirements=[],
            feature_title="F",
            prd_id="my_prd_001",
            feature_id="my_feat_001",
        )
        assert prd_id == "my_prd_001"
        assert feat_id == "my_feat_001"
        assert store.get("my_prd_001") is not None


class TestPRDIngesterFromFile:
    def test_ingest_markdown_file(self, ingester, store, tmp_path):
        md = tmp_path / "prd_bgp_gr.md"
        md.write_text(
            "# BGP Graceful Restart\n\n"
            "Implement GR support as per RFC 4724.\n\n"
            "- Must support all address families\n"
            "- Should handle stale routes for up to 300 seconds\n"
            "- Must not cause session reset\n"
        )
        prd_id, feat_id = ingester.ingest_from_file(
            prd_path=str(md),
            feature_title="BGP GR Support",
        )
        data = store.get(prd_id)
        assert data["title"] == "BGP Graceful Restart"
        assert len(data["requirements"]) == 3

    def test_ingest_json_file(self, ingester, store, tmp_path):
        prd_data = {
            "prd_id": "prd_json_001",
            "title": "JSON PRD Feature",
            "description": "A feature from JSON",
            "requirements": [{"id": "REQ-001", "description": "Do the thing", "priority": "must"}],
        }
        json_file = tmp_path / "prd.json"
        json_file.write_text(json.dumps(prd_data))

        prd_id, _ = ingester.ingest_from_file(
            prd_path=str(json_file),
            feature_title="JSON Feature",
        )
        assert prd_id == "prd_json_001"
        data = store.get(prd_id)
        assert data["title"] == "JSON PRD Feature"

    def test_missing_file_raises(self, ingester):
        with pytest.raises(FileNotFoundError):
            ingester.ingest_from_file("/nonexistent/prd.md", feature_title="test")


class TestPRDIngesterLoadExisting:
    def test_existing_artifacts_pass_through(self, ingester, store):
        store.store("prd_001", "prd_ingestion", "PRD", {"title": "existing"})
        store.store("feat_001", "prd_ingestion", "FeatureRequest", {"title": "existing feature"})
        prd_id, feat_id = ingester.load_existing("prd_001", "feat_001")
        assert prd_id == "prd_001"
        assert feat_id == "feat_001"

    def test_missing_prd_raises(self, ingester, store):
        store.store("feat_001", "prd_ingestion", "FeatureRequest", {})
        with pytest.raises(KeyError, match="prd_missing"):
            ingester.load_existing("prd_missing", "feat_001")

    def test_missing_feature_raises(self, ingester, store):
        store.store("prd_001", "prd_ingestion", "PRD", {})
        with pytest.raises(KeyError, match="feat_missing"):
            ingester.load_existing("prd_001", "feat_missing")
