"""Task definitions for Test Plan generation (Stage 5) and review (Stage 6)."""

try:
    from crewai import Task
except ImportError:  # allows importing tasks without CrewAI (fake-crew tests)
    Task = None
from typing import Optional


def test_plan_generation_task(
    agent,
    fs_id: str,
    topology_id: str,
    impl_summary_id: Optional[str] = None,
    testing_notes_id: Optional[str] = None,
    context: Optional[list] = None
) -> Task:
    impl_ctx = f"Implementation Summary (artifact_id: {impl_summary_id})" if impl_summary_id else "No implementation summary available."
    notes_ctx = f"Testing Notes (artifact_id: {testing_notes_id})" if testing_notes_id else "No testing notes available."

    return Task(
        description=f"""
        Generate a comprehensive test plan from:
        - FS (artifact_id: {fs_id})
        - Topology (artifact_id: {topology_id})
        - {impl_ctx}
        - {notes_ctx}

        Steps:
        1. Retrieve all available artifacts.
        2. For each FS functional requirement, derive at least:
           - 1 positive test scenario
           - 1 negative test scenario
           - Edge cases where applicable
        3. Define expected results for each scenario.
        4. Map each scenario back to its FS requirement (coverage_mapping).
        5. List topology requirements per scenario.
        6. Compute overall coverage percentage.
        7. Store the TestPlan artifact with stage_id='test_plan_gen'.

        Output format (JSON):
        {{
          "test_scenarios": [
            {{"id": "TC-001", "name": "...", "steps": [...], "fs_req_id": "FR-001", "type": "positive"}}
          ],
          "expected_results": [{{"tc_id": "TC-001", "expected": "..."}}],
          "coverage_mapping": {{"FR-001": ["TC-001", "TC-002"]}},
          "topology_requirements": ["2 CORE devices", "L3 adjacency"]
        }}
        """,
        expected_output="TestPlan artifact stored with full scenario set, coverage mapping, and artifact_id returned.",
        agent=agent,
        context=context or [],
    )


def test_plan_review_task(agent, test_plan_id: str, fs_id: str, context: Optional[list] = None) -> Task:
    return Task(
        description=f"""
        Review and coordinate approval of the test plan (artifact_id: {test_plan_id}).
        Reference FS (artifact_id: {fs_id}).

        Steps:
        1. Retrieve the TestPlan and FS.
        2. Score coverage (0-10): does the plan cover all FS requirements?
        3. Identify missing scenarios, incorrect expected results, or unclear steps.
        4. Collect reviewer comments.
        5. Request approval from QA Lead, PM, and DEV Lead via notification.
        6. Record approval decision (approved/rejected).
        7. Store the approved TestPlan with approved=true if all criteria met.
        8. Feed comments back to test_plan_gen stage if rejected.

        Output format (JSON):
        {{
          "coverage_score": 9.0,
          "reviewer_comments": ["comment1"],
          "approved": true,
          "feedback_for_revision": []
        }}
        """,
        expected_output="TestPlan review result stored with approval decision and artifact_id returned.",
        agent=agent,
        context=context or [],
        human_input=True,
    )
