"""Task definitions for Phase 1: Scoping stages (1a DEV, 1b QA)."""

try:
    from crewai import Task
except ImportError:  # allows importing tasks without CrewAI (fake-crew tests)
    Task = None
from typing import Optional


def dev_scoping_task(
    agent, prd_id: str, feature_request_id: str, context: Optional[list] = None
) -> Task:
    return Task(
        description=f"""
        Analyze the PRD (artifact_id: {prd_id}) and feature request (artifact_id: {feature_request_id}).

        Steps:
        1. Retrieve both artifacts using the artifact store tool.
        2. Determine scope decision: in-scope / out-of-scope / partial.
        3. Provide a clear rationale referencing specific requirements.
        4. Generate a concise feature_short_name (2-4 words, snake_case).
        5. Classify the technology stack (language, framework, protocol, topology type).
        6. Define explicit scope boundaries and constraints.
        7. Store the ScopingDecision artifact with stage_id='scoping_dev'.

        Output format (JSON):
        {{
          "decision": "in-scope|out-of-scope|partial",
          "rationale": "...",
          "feature_short_name": "...",
          "technology_classification": {{"language": "...", "framework": "..."}},
          "scope_boundaries": ["boundary1", "boundary2"]
        }}
        """,
        expected_output="ScopingDecision artifact stored and its artifact_id returned.",
        agent=agent,
        context=context or [],
    )


def qa_scoping_task(
    agent, scoping_decision_id: str, prd_id: Optional[str] = None, context: Optional[list] = None
) -> Task:
    return Task(
        description=f"""
        Enrich the DEV scoping decision (artifact_id: {scoping_decision_id}) with test perspective.

        Steps:
        1. Retrieve the DEV ScopingDecision artifact.
        2. Assess testability: what can be tested, what cannot, and why.
        3. Define the coverage scope: functional, negative, edge-case, performance areas.
        4. Evaluate automation feasibility: full / partial / manual-only.
        5. Identify topology requirements: device types, count, connection types.
        6. Produce an updated scoping decision if QA perspective changes boundaries.
        7. Store the TestConsiderations artifact with stage_id='scoping_qa'.

        Output format (JSON):
        {{
          "testability_assessment": "...",
          "coverage_scope": ["area1", "area2"],
          "automation_feasibility": "full|partial|manual-only",
          "topology_requirements": ["req1", "req2"],
          "updated_scope_notes": "..."
        }}
        """,
        expected_output="TestConsiderations artifact stored and its artifact_id returned.",
        agent=agent,
        context=context or [],
    )
