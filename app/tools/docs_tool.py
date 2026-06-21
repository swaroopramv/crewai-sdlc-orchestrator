"""Documentation tools — read/write artifacts from the shared artifact store."""

import json

from crewai.tools import BaseTool


class ArtifactReadTool(BaseTool):
    name: str = "read_artifact"
    description: str = "Read an artifact from the artifact store by its artifact_id and return its content"
    _artifact_store: object = None

    def __init__(self, artifact_store):
        super().__init__()
        self._artifact_store = artifact_store

    def _run(self, artifact_id: str) -> str:
        data = self._artifact_store.get(artifact_id)
        if data is None:
            return json.dumps({"error": f"Artifact {artifact_id} not found"})
        return json.dumps(data)


class ArtifactWriteTool(BaseTool):
    name: str = "write_artifact"
    description: str = "Store an artifact in the artifact store with the given stage_id and artifact_type"
    _artifact_store: object = None

    def __init__(self, artifact_store):
        super().__init__()
        self._artifact_store = artifact_store

    def _run(self, artifact_id: str, stage_id: str, artifact_type: str, data: dict) -> str:
        stored_id = self._artifact_store.store(artifact_id, stage_id, artifact_type, data)
        return json.dumps({"artifact_id": stored_id, "status": "stored"})


def get_docs_tools(artifact_store) -> list:
    return [ArtifactReadTool(artifact_store), ArtifactWriteTool(artifact_store)]
