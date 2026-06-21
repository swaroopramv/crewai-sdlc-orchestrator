"""Task definitions for Stage (10) and Execute (11)."""

try:
    from crewai import Task
except ImportError:  # allows importing tasks without CrewAI (fake-crew tests)
    Task = None
from typing import Optional


def stage_task(
    agent, test_project_id: str, testbed_id: str, context: Optional[list] = None
) -> Task:
    return Task(
        description=f"""
        Stage the test project (artifact_id: {test_project_id}) to the execution environment.
        Testbed: (artifact_id: {testbed_id})

        Steps:
        1. Retrieve the test project and testbed artifacts.
        2. Validate test project structure is complete (scripts, testdata, testbed YAML).
        3. Commit the project to CI using the ci_tool.
        4. Capture the CI commit reference (job ID / URL).
        5. Verify staging was successful (no errors in CI response).
        6. Store the stage result with stage_id='stage'.

        Output format (JSON):
        {{
          "stage_result": "success|failed",
          "ci_commit_ref": "https://ci.example.com/job/12345",
          "staging_log": "..."
        }}
        """,
        expected_output="Stage result artifact stored with ci_commit_ref and artifact_id returned.",
        agent=agent,
        context=context or [],
    )


def execute_task(
    agent, stage_result_id: str, testbed_id: str, context: Optional[list] = None
) -> Task:
    return Task(
        description=f"""
        Execute the staged test suite using CI.
        Stage result (artifact_id: {stage_result_id})
        Testbed (artifact_id: {testbed_id})

        Steps:
        1. Retrieve stage result to get CI commit reference.
        2. Trigger execution via the ci_tool using the commit reference.
        3. Monitor execution progress until completion.
        4. Collect pass/fail counts per testcase.
        5. Download logs for failed testcases.
        6. Compute pass_rate = (pass_count / total_count) * 100.
        7. Store the ExecutionResult artifact with stage_id='execute'.

        Output format (JSON):
        {{
          "pass_count": 45,
          "fail_count": 5,
          "total_count": 50,
          "pass_rate": 90.0,
          "ci_ref": "...",
          "logs": ["FAILED TC-015: ...", "FAILED TC-022: ..."]
        }}
        """,
        expected_output="ExecutionResult artifact stored with pass/fail counts, pass_rate, logs, and artifact_id returned.",
        agent=agent,
        context=context or [],
    )
