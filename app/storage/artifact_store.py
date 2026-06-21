"""Artifact storage — persists and retrieves all SDLC artifacts."""

from __future__ import annotations
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Any


class ArtifactStore:
    """
    Simple SQLite-backed artifact store.
    Swap the backend by replacing _write / _read with S3 or PostgreSQL calls.
    """

    def __init__(self, db_path: str = "artifacts.db"):
        self._db_path = db_path
        self._init_db()

    def _init_db(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    stage_id    TEXT NOT NULL,
                    artifact_type TEXT NOT NULL,
                    data        TEXT NOT NULL,
                    created_at  TEXT NOT NULL,
                    version     INTEGER DEFAULT 1
                )
            """)

    def _conn(self):
        return sqlite3.connect(self._db_path)

    def store(self, artifact_id: str, stage_id: str, artifact_type: str, data: Any, version: int = 1) -> str:
        payload = data if isinstance(data, str) else json.dumps(data, default=str)
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO artifacts VALUES (?,?,?,?,?,?)",
                (artifact_id, stage_id, artifact_type, payload, datetime.utcnow().isoformat(), version)
            )
        return artifact_id

    def get(self, artifact_id: str) -> Optional[dict]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT data FROM artifacts WHERE artifact_id=?", (artifact_id,)
            ).fetchone()
        if not row:
            return None
        try:
            return json.loads(row[0])
        except json.JSONDecodeError:
            return {"raw": row[0]}

    def list_by_stage(self, stage_id: str) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT artifact_id, artifact_type, created_at FROM artifacts WHERE stage_id=?",
                (stage_id,)
            ).fetchall()
        return [{"artifact_id": r[0], "type": r[1], "created_at": r[2]} for r in rows]

    def delete(self, artifact_id: str) -> bool:
        with self._conn() as conn:
            cursor = conn.execute("DELETE FROM artifacts WHERE artifact_id=?", (artifact_id,))
        return cursor.rowcount > 0
