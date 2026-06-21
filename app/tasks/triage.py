"""Task definitions for the Triage Loop: Triage (12), Bug File (13), Bug Repro (14), Fix (15), FixVerify (16)."""

try:
    from crewai import Task
except ImportError:  # allows importing tasks without CrewAI (fake-crew tests)
    Task = None
from typing import Optional


def triage_task(agent, execution_id: str, scripts_id: str, context: Optional[list] = None) -> Task:
    return Task(
        description=f"""
        Analyze test failures from execution (artifact_id: {execution_id}).
        Test scripts (artifact_id: {scripts_id})

        Steps:
        1. Retrieve execution result and test scripts.
        2. For each failed testcase, analyze the log to classify root cause:
           - PRODUCT_BUG: defect in the product code
           - TEST_ISSUE: bug in test script logic
           - ENV_ISSUE: testbed or environment problem
           - INFRA_ISSUE: CI or infrastructure problem
        3. Perform root cause analysis for product bugs.
        4. Separate product_bugs list from test_issues list.
        5. Store the TriageReport artifact with stage_id='triage'.

        Output format (JSON):
        {{
          "failure_classifications": [
            {{"tc_id": "TC-015", "type": "PRODUCT_BUG", "summary": "..."}}
          ],
          "root_cause_analysis": ["RCA for bug 1: ..."],
          "product_bugs": ["TC-015"],
          "test_issues": ["TC-022"]
        }}
        """,
        expected_output="TriageReport artifact stored with classified failures and artifact_id returned.",
        agent=agent,
        context=context or [],
    )


def bug_file_task(agent, triage_id: str, context: Optional[list] = None) -> Task:
    return Task(
        description=f"""
        File IssueTracker bug records for confirmed product bugs from triage (artifact_id: {triage_id}).

        Steps:
        1. Retrieve the TriageReport.
        2. For each product_bug in the report, create a BugRecord:
           - Write a clear, concise title.
           - Write a full description with observed vs expected behavior.
           - Set severity (S1/S2/S3/S4) and priority (P1/P2/P3/P4).
           - List reproduction steps.
        3. File each bug via the bug_tool (IssueTracker MCP).
        4. Capture the returned issue_tracker_id for each bug.
        5. Store each BugRecord artifact with stage_id='bug_file'.

        Output: List of BugRecord artifact_ids filed.
        """,
        expected_output="BugRecord artifacts stored with issue_tracker_ids and list of artifact_ids returned.",
        agent=agent,
        context=context or [],
    )


def bug_repro_task(agent, bug_record_id: str, scripts_id: str, testbed_id: str, context: Optional[list] = None) -> Task:
    return Task(
        description=f"""
        Reproduce the filed bug (artifact_id: {bug_record_id}).
        Test scripts (artifact_id: {scripts_id})
        Testbed (artifact_id: {testbed_id})

        Steps:
        1. Retrieve the BugRecord, test scripts, and testbed.
        2. Isolate the failing testcase.
        3. Execute the failing test in a controlled environment via ci_tool.
        4. Confirm whether the bug is reproducible.
        5. Document step-by-step reproduction instructions.
        6. Capture environment details (SW version, topology, config).
        7. Store the ReproResult artifact with stage_id='bug_repro'.

        Output format (JSON):
        {{
          "reproduced": true,
          "reproduction_steps": ["step1", "step2"],
          "environment_details": {{"sw_version": "...", "topology": "..."}}
        }}
        """,
        expected_output="ReproResult artifact stored with reproduction steps and artifact_id returned.",
        agent=agent,
        context=context or [],
    )


def fix_task(agent, bug_record_id: str, repro_result_id: str, scripts_id: str, context: Optional[list] = None) -> Task:
    return Task(
        description=f"""
        Apply a fix for the confirmed bug (artifact_id: {bug_record_id}).
        Reproduction result (artifact_id: {repro_result_id})
        Test scripts (artifact_id: {scripts_id})

        Steps:
        1. Retrieve BugRecord, ReproResult, and test scripts.
        2. Determine if fix is:
           - Product code fix (DEV responsibility)
           - Test script fix (QA responsibility)
        3. Apply the targeted fix without introducing regressions.
        4. Document all code changes in the patch description.
        5. If test scripts were updated, list updated_script_ids.
        6. Store the FixPatch artifact with stage_id='fix'.
        7. Update the IssueTracker bug record status via bug_tool.

        Output format (JSON):
        {{
          "description": "Fixed null pointer in feature handler",
          "code_changes": {{"file": "changes"}},
          "updated_script_ids": []
        }}
        """,
        expected_output="FixPatch artifact stored with code_changes and artifact_id returned.",
        agent=agent,
        context=context or [],
        human_input=True,
    )


def fix_verify_task(agent, patch_id: str, execution_id: str, context: Optional[list] = None) -> Task:
    return Task(
        description=f"""
        Validate that the fix (artifact_id: {patch_id}) resolves the issue and causes no regressions.
        Reference execution (artifact_id: {execution_id})

        Steps:
        1. Retrieve the FixPatch and original ExecutionResult.
        2. Re-execute the previously failing testcases via ci_tool.
        3. Run the full regression suite on the fixed code.
        4. Check:
           - Previously failing TCs now pass → validation_passed = true
           - Previously passing TCs still pass → regression_detected = false
        5. Write a validation_summary.
        6. Store the R2VResult artifact with stage_id='fix_verify'.
        7. Update the IssueTracker bug status to 'fixed' via bug_tool if validation passed.

        Output format (JSON):
        {{
          "validation_passed": true,
          "regression_detected": false,
          "validation_summary": "All 5 previously failing TCs now pass. No regressions detected."
        }}
        """,
        expected_output="R2VResult artifact stored with validation_passed, regression_detected, and artifact_id returned.",
        agent=agent,
        context=context or [],
    )
