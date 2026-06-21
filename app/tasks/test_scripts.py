"""Task definitions for test script generation (Stage 7), review (Stage 8), and Coverage (Stage 9)."""

try:
    from crewai import Task
except ImportError:  # allows importing tasks without CrewAI (fake-crew tests)
    Task = None
from typing import Optional


def test_script_generation_task(
    agent,
    test_plan_id: str,
    topology_id: str,
    impl_summary_id: Optional[str] = None,
    automation_notes_id: Optional[str] = None,
    context: Optional[list] = None,
) -> Task:
    impl_ctx = f"Implementation Summary (artifact_id: {impl_summary_id})" if impl_summary_id else ""
    auto_ctx = (
        f"Automation Notes (artifact_id: {automation_notes_id})" if automation_notes_id else ""
    )

    return Task(
        description=f"""
        Generate executable pytest test scripts from:
        - Approved Test Plan (artifact_id: {test_plan_id})
        - Topology (artifact_id: {topology_id})
        - {impl_ctx}
        - {auto_ctx}

        Steps:
        1. Retrieve all artifacts.
        2. For each test scenario in the test plan, generate a pytest testcase class.
        3. Use topology info to generate testbed YAML structure.
        4. Create reusable library functions for common operations.
        5. Generate test data files (YAML/JSON) for parameterized tests.
        6. Define a project structure: tests/, lib/, testdata/, testbed/.
        7. Ensure all scripts follow the test framework coding standards.
        8. Store the TestScripts artifact with stage_id='test_script_gen'.

        pytest script format:
        - Each testcase inherits from aetest.Testcase
        - setup/test/cleanup sections defined
        - Assertions use self.failed() / self.passed()
        - Device access via testbed.devices['device_name']

        Output: TestScripts artifact_id and project_structure summary.
        """,
        expected_output="TestScripts artifact stored with script_paths, libraries, testdata, project_structure and artifact_id returned.",
        agent=agent,
        context=context or [],
    )


def test_script_review_task(
    agent, scripts_id: str, test_plan_id: str, context: Optional[list] = None
) -> Task:
    return Task(
        description=f"""
        Review the generated test scripts (artifact_id: {scripts_id}) against the test plan (artifact_id: {test_plan_id}).

        Review criteria:
        1. Correctness: does each script correctly implement its test scenario?
        2. Standards compliance: the test framework conventions, naming, docstrings.
        3. Coverage alignment: does the script set cover all planned scenarios?
        4. Robustness: are there try/except blocks, cleanup handlers?
        5. Test independence: each test should be runnable standalone.

        Steps:
        1. Retrieve scripts and test plan.
        2. Score correctness (0-10) and standards compliance (0-10).
        3. List specific comments per script file.
        4. Set approved=true only if both scores ≥ 7.
        5. Store the TestScriptReview artifact with stage_id='test_script_review'.

        Output format (JSON):
        {{
          "correctness_score": 8.5,
          "standards_score": 9.0,
          "review_comments": [{{"file": "test_feature.py", "comment": "..."}}],
          "approved": true
        }}
        """,
        expected_output="TestScriptReview artifact stored with scores, comments, approval, and artifact_id returned.",
        agent=agent,
        context=context or [],
    )


def coverage_check_task(
    agent, scripts_id: str, test_plan_id: str, context: Optional[list] = None
) -> Task:
    return Task(
        description=f"""
        Measure test coverage of scripts (artifact_id: {scripts_id}) against the test plan (artifact_id: {test_plan_id}).

        Steps:
        1. Retrieve test scripts and test plan.
        2. For each test scenario in the plan, check if a corresponding script exists.
        3. Compute coverage_percentage = (covered_scenarios / total_scenarios) * 100.
        4. List uncovered scenarios as coverage_gaps.
        5. Build scenario_coverage map: {{"TC-001": true, "TC-002": false}}.
        6. Store the CTCResult artifact with stage_id='coverage_check'.

        Output format (JSON):
        {{
          "coverage_percentage": 92.5,
          "coverage_gaps": ["TC-015", "TC-022"],
          "scenario_coverage": {{"TC-001": true, "TC-002": false}}
        }}
        """,
        expected_output="CTCResult artifact stored with coverage percentage, gaps, and artifact_id returned.",
        agent=agent,
        context=context or [],
    )
