"""Checkpoint store — saves and loads PipelineState for resume capability."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Optional

from models.pipeline_state import PipelineState


class CheckpointStore:
    def __init__(self, db_path: str = "checkpoints.db"):
        self._db_path = db_path
        self._init_db()

    def _init_db(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    checkpoint_id TEXT PRIMARY KEY,
                    pipeline_id   TEXT NOT NULL,
                    state_json    TEXT NOT NULL,
                    created_at    TEXT NOT NULL,
                    description   TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_pipeline ON checkpoints(pipeline_id)")

    def _conn(self):
        return sqlite3.connect(self._db_path)

    def save(self, state: PipelineState, description: str = "") -> str:
        checkpoint_id = f"{state.pipeline_id}_{datetime.utcnow().timestamp()}"
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO checkpoints VALUES (?,?,?,?,?)",
                (
                    checkpoint_id,
                    state.pipeline_id,
                    state.model_dump_json(),
                    datetime.utcnow().isoformat(),
                    description,
                )
            )
        return checkpoint_id

    def load_latest(self, pipeline_id: str) -> Optional[PipelineState]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT state_json FROM checkpoints WHERE pipeline_id=? ORDER BY created_at DESC LIMIT 1",
                (pipeline_id,)
            ).fetchone()
        if not row:
            return None
        return PipelineState.model_validate_json(row[0])

    def list_checkpoints(self, pipeline_id: str) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT checkpoint_id, created_at, description FROM checkpoints WHERE pipeline_id=? ORDER BY created_at DESC",
                (pipeline_id,)
            ).fetchall()
        return [{"id": r[0], "created_at": r[1], "description": r[2]} for r in rows]

    def delete_old(self, pipeline_id: str, keep: int = 5) -> int:
        checkpoints = self.list_checkpoints(pipeline_id)
        to_delete = checkpoints[keep:]
        if not to_delete:
            return 0
        with self._conn() as conn:
            for cp in to_delete:
                conn.execute("DELETE FROM checkpoints WHERE checkpoint_id=?", (cp["id"],))
        return len(to_delete)

    def cleanup(self, pipeline_id: str) -> int:
        with self._conn() as conn:
            cursor = conn.execute("DELETE FROM checkpoints WHERE pipeline_id=?", (pipeline_id,))
        return cursor.rowcount
