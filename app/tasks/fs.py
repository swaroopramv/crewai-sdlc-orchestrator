"""Task definitions for FS generation (Stage 2) and FS review (Stage 4)."""

try:
    from crewai import Task
except ImportError:  # allows importing tasks without CrewAI (fake-crew tests)
    Task = None
from typing import Optional


def fs_generation_task(
    agent, prd_id: str, scoping_dev_id: str, scoping_qa_id: str, context: Optional[list] = None
) -> Task:
    return Task(
        description=f"""
        Generate the Software Functional Specification (FS) from:
        - PRD (artifact_id: {prd_id})
        - DEV Scoping Decision (artifact_id: {scoping_dev_id})
        - QA Test Considerations (artifact_id: {scoping_qa_id})

        Steps:
        1. Retrieve all three artifacts.
        2. Derive EARS-style functional requirements from the PRD.
        3. Derive non-functional requirements (performance, scale, security).
        4. Build a traceability matrix: PRD requirement ID → FS requirement ID.
        5. Ensure every requirement is specific, measurable, and testable.
        6. Store the FS artifact with stage_id='fs_gen'.

        Output format (JSON):
        {{
          "title": "...",
          "feature_description": "...",
          "functional_requirements": [{{"id": "FR-001", "description": "...", "priority": "must"}}],
          "non_functional_requirements": [{{"id": "NFR-001", "description": "..."}}],
          "traceability_matrix": {{"PRD-001": "FR-001"}}
        }}
        """,
        expected_output="FS artifact stored with full traceability matrix and its artifact_id returned.",
        agent=agent,
        context=context or [],
    )


def dev_feature_track_task(agent, prd_id: str, fs_id: str, context: Optional[list] = None) -> Task:
    return Task(
        description=f"""
        Implement the feature described in:
        - PRD (artifact_id: {prd_id})
        - FS (artifact_id: {fs_id})

        Steps:
        1. Retrieve PRD and FS artifacts.
        2. Produce a high-level implementation plan.
        3. Write an implementation summary (key decisions, modules changed).
        4. Write testing notes: what to focus on, known risks, tricky areas.
        5. Write automation notes: APIs available, CLI commands, MIBs, parsers needed.
        6. Store the ImplArtifacts with stage_id='dev_feature_track'.

        Output format (JSON):
        {{
          "impl_plan": "...",
          "impl_summary": "...",
          "testing_notes": "...",
          "automation_notes": "..."
        }}
        """,
        expected_output="ImplArtifacts stored with impl_summary, testing_notes, automation_notes and artifact_id returned.",
        agent=agent,
        context=context or [],
    )


def fs_review_task(
    agent,
    fs_id: str,
    prd_id: str,
    traceability_id: Optional[str] = None,
    context: Optional[list] = None,
) -> Task:
    return Task(
        description=f"""
        Review the FS (artifact_id: {fs_id}) against the PRD (artifact_id: {prd_id}).

        Steps:
        1. Retrieve the FS and PRD.
        2. Score completeness (0-10): all functional areas covered?
        3. Score correctness (0-10): requirements clear, non-contradictory, verifiable?
        4. Identify test-readiness gaps: requirements that cannot yet be tested.
        5. Produce actionable review comments for each gap.
        6. Mark approved=true only if completeness ≥ 7 and correctness ≥ 7 with no critical gaps.
        7. Store the SFSReviewReport with stage_id='fs_review'.
        8. Send notification to DEV with review comments.

        Output format (JSON):
        {{
          "completeness_score": 8.5,
          "correctness_score": 9.0,
          "test_readiness_gaps": ["gap1", "gap2"],
          "review_comments": ["comment1", "comment2"],
          "approved": true
        }}
        """,
        expected_output="SFSReviewReport stored with scores, gaps, comments and artifact_id returned.",
        agent=agent,
        context=context or [],
    )
