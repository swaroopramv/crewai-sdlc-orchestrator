"""Task definitions for Phase 5 release stages (17-24)."""

from crewai import Task
from typing import Optional


def support_kt_task(agent, fix_verify_id: str, test_plan_id: str, execution_id: str, context: Optional[list] = None) -> Task:
    return Task(
        description=f"""
        Generate a Support Knowledge Transfer (KT) document.
        FixVerify result (artifact_id: {fix_verify_id})
        Test plan (artifact_id: {test_plan_id})
        Execution result (artifact_id: {execution_id})

        Steps:
        1. Retrieve all three artifacts.
        2. Write a KT covering:
           - Feature overview (what it does, why it matters)
           - Known issues, limitations, and workarounds
           - Supported and unsupported configurations
           - Common customer failure scenarios and resolutions
           - CLI show commands for diagnosis
        3. Store the TACTOIDoc artifact with stage_id='support_kt'.

        Output: TACTOIDoc artifact_id and content summary.
        """,
        expected_output="TACTOIDoc artifact stored with full KT content and artifact_id returned.",
        agent=agent,
        context=context or [],
    )


def docs_task(agent, fs_id: str, test_plan_id: str, execution_id: str, context: Optional[list] = None) -> Task:
    return Task(
        description=f"""
        Generate feature documentation and release notes.
        FS (artifact_id: {fs_id})
        Test Plan (artifact_id: {test_plan_id})
        Execution Result (artifact_id: {execution_id})

        Steps:
        1. Retrieve all artifacts.
        2. Write feature documentation:
           - Overview and use cases
           - Configuration guide with CLI examples
           - Verification steps
           - Troubleshooting section
        3. Write release notes:
           - New feature description
           - Caveats and restrictions
           - Bug fixes (from execution results)
        4. Store the FeatureDocs artifact with stage_id='docs_gen'.

        Output: FeatureDocs artifact_id.
        """,
        expected_output="FeatureDocs artifact stored with documentation content and release_notes. Artifact_id returned.",
        agent=agent,
        context=context or [],
    )


def coverage_final_task(agent, execution_id: str, test_plan_id: str, coverage_check_id: str, context: Optional[list] = None) -> Task:
    return Task(
        description=f"""
        Produce the final Coverage coverage report after all execution cycles.
        Execution result (artifact_id: {execution_id})
        Test plan (artifact_id: {test_plan_id})
        Initial Coverage result (artifact_id: {coverage_check_id})

        Steps:
        1. Retrieve all artifacts.
        2. Compute final coverage_percentage over all executed tests.
        3. Compute coverage_delta vs initial Coverage check.
        4. List any remaining coverage_gaps.
        5. Store the final CTCResult with stage_id='coverage_final'.

        Output format (JSON):
        {{
          "coverage_percentage": 97.5,
          "coverage_delta": "+5.0%",
          "coverage_gaps": [],
          "scenario_coverage": {{"TC-001": true}}
        }}
        """,
        expected_output="Final CTCResult stored with coverage_percentage, delta, remaining gaps, and artifact_id returned.",
        agent=agent,
        context=context or [],
    )


def sit_task(agent, test_project_id: str, execution_id: str, context: Optional[list] = None) -> Task:
    return Task(
        description=f"""
        Run System Integration Tests (SIT) to validate end-to-end behavior.
        Test project (artifact_id: {test_project_id})
        Previous execution result (artifact_id: {execution_id})

        Steps:
        1. Retrieve test project and execution result.
        2. Execute integration test suite on the full integrated environment via ci_tool.
        3. Validate feature interoperability with dependent features.
        4. Collect SIT pass/fail and integration report.
        5. Store the SIT result with stage_id='sit'.

        Output: SIT result artifact_id and pass/fail summary.
        """,
        expected_output="SIT result artifact stored with integration_report and artifact_id returned.",
        agent=agent,
        context=context or [],
    )


def nightly_integration_task(agent, test_project_id: str, sit_result_id: str, context: Optional[list] = None) -> Task:
    return Task(
        description=f"""
        Integrate the validated tests into nightly and regression suites.
        Test project (artifact_id: {test_project_id})
        SIT result (artifact_id: {sit_result_id})

        Steps:
        1. Retrieve test project and SIT result.
        2. Confirm SIT passed before integration.
        3. Create a nightly profile YAML for the new test suite.
        4. Update the regression suite manifest to include new testcases.
        5. Register profile with the nightly scheduler via ci_tool.
        6. Store the nightly integration result with stage_id='nightly_integration'.

        Output: Nightly profile artifact_id and regression suite update summary.
        """,
        expected_output="Nightly profile artifact stored with regression_suite_update and artifact_id returned.",
        agent=agent,
        context=context or [],
    )


def nightly_reporting_task(agent, nightly_profile_id: str, execution_id: str, context: Optional[list] = None) -> Task:
    return Task(
        description=f"""
        Report on nightly/regression run results and trends.
        Nightly profile (artifact_id: {nightly_profile_id})
        Execution result (artifact_id: {execution_id})

        Steps:
        1. Retrieve nightly profile and execution result.
        2. Generate nightly report: pass rate, new failures, flaky tests.
        3. Produce trend analysis across last 5 runs if data available.
        4. Highlight any regressions introduced.
        5. Send report via notification_tool to QA team.
        6. Store the nightly report artifact with stage_id='nightly_reporting'.

        Output: Nightly report artifact_id and trend_analysis summary.
        """,
        expected_output="Nightly report artifact stored with trend_analysis and artifact_id returned.",
        agent=agent,
        context=context or [],
    )


def qa_signoff_task(
    agent,
    kt_id: str,
    docs_id: str,
    coverage_final_id: str,
    sit_result_id: str,
    nightly_report_id: str,
    context: Optional[list] = None
) -> Task:
    return Task(
        description=f"""
        Aggregate all release artifacts and coordinate QA/FCS sign-off.
        Support KT (artifact_id: {kt_id})
        Feature Docs (artifact_id: {docs_id})
        Final Coverage (artifact_id: {coverage_final_id})
        SIT Result (artifact_id: {sit_result_id})
        Nightly Report (artifact_id: {nightly_report_id})

        Steps:
        1. Retrieve all release artifacts.
        2. Verify each artifact is present and approved.
        3. Compile QA artifact bundle and FCS artifact bundle.
        4. Request QA sign-off from QA Manager and QA Lead via approval_tool.
        5. Record sign-off decision and timestamp.
        6. Send sign-off notification to release management.
        7. Store the DTESignoff artifact with stage_id='qa_signoff'.

        Output: DTESignoff artifact_id and signoff status.
        """,
        expected_output="DTESignoff artifact stored with status, signed_by, and artifact_id returned.",
        agent=agent,
        context=context or [],
        human_input=True,
    )


def feedback_task(agent, pipeline_id: str, context: Optional[list] = None) -> Task:
    return Task(
        description=f"""
        Collect end-of-lifecycle feedback for pipeline: {pipeline_id}.

        Steps:
        1. Gather metrics from all completed stages (duration, retries, failures).
        2. Identify which stages had the most retries or failures.
        3. Identify which stages benefited most from optional artifacts.
        4. Synthesize improvement suggestions.
        5. Compute an overall pipeline quality rating (0-10).
        6. Store the FeedbackReport artifact with stage_id='feedback'.

        Output format (JSON):
        {{
          "overall_rating": 8.5,
          "stage_feedback": {{"fs_review": "Good coverage identification", "triage": "Accurate classification"}},
          "suggestions": ["Automate topology provisioning", "Add pre-validation before execution"]
        }}
        """,
        expected_output="FeedbackReport artifact stored with overall_rating, stage_feedback, suggestions, and artifact_id returned.",
        agent=agent,
        context=context or [],
    )
