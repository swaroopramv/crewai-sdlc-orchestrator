"""CI integration tool for test staging and execution."""

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class CIStagingInput(BaseModel):
    project_path: str = Field(..., description="Path to the test project directory")
    testbed_id: str = Field(..., description="Testbed identifier")
    test_suite: str = Field(
        default="all", description="Test suite to stage (all or specific TC ID)"
    )


class CIExecutionInput(BaseModel):
    commit_ref: str = Field(..., description="CI commit reference or job ID")
    testbed_id: str = Field(..., description="Testbed identifier")
    timeout_minutes: int = Field(default=120, description="Execution timeout in minutes")


class CIStageTool(BaseTool):
    name: str = "ci_stage"
    description: str = (
        "Stage a test project to the CI execution environment and get a commit reference"
    )

    def _run(self, project_path: str, testbed_id: str, test_suite: str = "all") -> str:
        """
        Stage test project to CI.
        In production: calls CI REST API to stage the project.
        """
        # Placeholder — replace with actual CI API call
        commit_ref = f"ci://commit/{testbed_id}/{test_suite}/mock_ref"
        return f'{{"status": "staged", "commit_ref": "{commit_ref}"}}'


class CIExecuteTool(BaseTool):
    name: str = "ci_execute"
    description: str = "Execute a staged test suite on CI and return execution results"

    def _run(self, commit_ref: str, testbed_id: str, timeout_minutes: int = 120) -> str:
        """
        Execute staged tests via CI.
        In production: polls CI API until execution completes.
        """
        # Placeholder — replace with actual CI API call
        return (
            '{"status": "completed", "pass_count": 45, "fail_count": 5, '
            '"total_count": 50, "pass_rate": 90.0, '
            f'"execution_id": "exec_{testbed_id}_001"}}'
        )


class CILogTool(BaseTool):
    name: str = "ci_get_logs"
    description: str = "Download logs for failed testcases from a CI execution"

    def _run(self, execution_id: str, tc_ids: list[str]) -> str:
        """
        Fetch logs for specific failed testcases.
        In production: downloads from CI log storage.
        """
        # Placeholder
        logs = {tc: f"FAILED {tc}: AssertionError — expected X got Y" for tc in tc_ids}
        import json

        return json.dumps(logs)


ci_tools = [CIStageTool(), CIExecuteTool(), CILogTool()]
