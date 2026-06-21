"""
PRD Ingester — Stage 0 (pre-pipeline).

Reads a PRD from a file (Markdown, plain text, or JSON) or raw text string,
parses it into the PRD + FeatureRequest Pydantic models, and stores both
in the ArtifactStore so all downstream stages can reference them by ID.
"""

from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path
from typing import Optional

from models.artifacts import PRD, ArtifactMeta, FeatureRequest, Ownership, StageID
from storage.artifact_store import ArtifactStore

logger = logging.getLogger(__name__)


class PRDIngester:
    """Ingests a PRD document and a feature request into the artifact store."""

    INGEST_STAGE = StageID.PRD_INGESTION

    def __init__(self, artifact_store: ArtifactStore):
        self._store = artifact_store

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ingest_from_file(
        self,
        prd_path: str,
        feature_title: str,
        feature_description: str = "",
        feature_priority: str = "medium",
        prd_id: Optional[str] = None,
        feature_id: Optional[str] = None,
    ) -> tuple[str, str]:
        """
        Read a PRD from a file and ingest it.

        Supports:
        - .json  — must match PRD schema keys
        - .md / .txt — treated as free-text; title taken from first heading or filename

        Returns:
            (prd_artifact_id, feature_artifact_id)
        """
        path = Path(prd_path)
        if not path.exists():
            raise FileNotFoundError(f"PRD file not found: {prd_path}")

        content = path.read_text(encoding="utf-8")

        if path.suffix == ".json":
            prd_data = json.loads(content)
            prd = PRD(**prd_data)
        else:
            prd = self._parse_text_prd(content, stem=path.stem, prd_id=prd_id)

        return self._store_both(
            prd, feature_title, feature_description, feature_priority, feature_id
        )

    def ingest_from_text(
        self,
        prd_title: str,
        prd_description: str,
        requirements: list[dict],
        feature_title: str,
        feature_description: str = "",
        feature_priority: str = "medium",
        prd_id: Optional[str] = None,
        feature_id: Optional[str] = None,
    ) -> tuple[str, str]:
        """
        Ingest a PRD supplied directly as structured data (no file needed).

        Returns:
            (prd_artifact_id, feature_artifact_id)
        """
        prd = PRD(
            prd_id=prd_id or f"prd_{uuid.uuid4().hex[:8]}",
            title=prd_title,
            description=prd_description,
            requirements=requirements,
            meta=self._meta(),
        )
        return self._store_both(
            prd, feature_title, feature_description, feature_priority, feature_id
        )

    def load_existing(self, prd_id: str, feature_id: str) -> tuple[str, str]:
        """
        Verify that existing PRD and FeatureRequest are already in the store.
        Raises KeyError if either is missing.

        Returns:
            (prd_id, feature_id) unchanged if both present.
        """
        if self._store.get(prd_id) is None:
            raise KeyError(f"PRD artifact '{prd_id}' not found in artifact store")
        if self._store.get(feature_id) is None:
            raise KeyError(f"FeatureRequest artifact '{feature_id}' not found in artifact store")
        logger.info(
            "PRD ingester: existing artifacts verified — prd=%s feature=%s", prd_id, feature_id
        )
        return prd_id, feature_id

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_text_prd(self, content: str, stem: str, prd_id: Optional[str]) -> PRD:
        """Parse a plain-text / Markdown PRD into a PRD model."""
        lines = content.strip().splitlines()

        # Extract title: first `# Heading` or fallback to filename stem
        title = stem.replace("_", " ").replace("-", " ").title()
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("# "):
                title = stripped.lstrip("# ").strip()
                break

        # Extract requirement bullets: lines starting with "- " or "* " or numbered "1. "
        requirements = []
        req_id = 1
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(("- ", "* ")) or (
                len(stripped) > 2 and stripped[0].isdigit() and stripped[1] in ".):"
            ):
                text = stripped.lstrip("-*0123456789.)").strip()
                if len(text) > 10:
                    requirements.append(
                        {"id": f"REQ-{req_id:03d}", "description": text, "priority": "must"}
                    )
                    req_id += 1

        return PRD(
            prd_id=prd_id or f"prd_{uuid.uuid4().hex[:8]}",
            title=title,
            description=content,
            requirements=requirements,
            meta=self._meta(),
        )

    def _store_both(
        self,
        prd: PRD,
        feature_title: str,
        feature_description: str,
        feature_priority: str,
        feature_id: Optional[str],
    ) -> tuple[str, str]:
        feature = FeatureRequest(
            request_id=feature_id or f"feat_{uuid.uuid4().hex[:8]}",
            title=feature_title,
            description=feature_description or feature_title,
            priority=feature_priority,
            meta=self._meta(),
        )

        self._store.store(prd.prd_id, self.INGEST_STAGE.value, "PRD", prd.model_dump())
        self._store.store(
            feature.request_id, self.INGEST_STAGE.value, "FeatureRequest", feature.model_dump()
        )

        logger.info(
            "PRD ingested → prd_id=%s  feature_id=%s  requirements=%d",
            prd.prd_id,
            feature.request_id,
            len(prd.requirements),
        )
        return prd.prd_id, feature.request_id

    def _meta(self) -> ArtifactMeta:
        return ArtifactMeta(
            stage_id=self.INGEST_STAGE,
            ownership=Ownership.ORCHESTRATOR,
            created_by="prd_ingester",
        )
