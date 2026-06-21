"""
Release phase agents.
Covers: Support KT (17), Docs (18), Coverage Final (19), SIT (20),
        Nightly Integration (21), Nightly Reporting (22), QA Sign-off (23), Feedback (24).
"""

from typing import Any

from crewai import Agent


def build_support_kt_agent(llm: Any, tools: list) -> Agent:
    return Agent(
        role="Support Knowledge Transfer Author",
        goal="Generate comprehensive Support KT documents that enable support teams to handle customer escalations for this feature",
        backstory=(
            "You are a technical writer with deep support experience. You know what Support engineers "
            "need: failure scenarios, diagnostic commands, workarounds, and known limitations. "
            "Your TOIs reduce escalation resolution time significantly."
        ),
        llm=llm,
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )


def build_docs_agent(llm: Any, tools: list) -> Agent:
    return Agent(
        role="Feature Documentation Engineer",
        goal="Generate accurate, user-friendly feature documentation and release notes from test artifacts and execution results",
        backstory=(
            "You are a technical writer who transforms complex test and implementation artifacts "
            "into clear user documentation. You write for network engineers: configuration examples, "
            "verification steps, and troubleshooting guidance."
        ),
        llm=llm,
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )


def build_coverage_final_agent(llm: Any, tools: list) -> Agent:
    return Agent(
        role="Final Coverage Report Analyst",
        goal="Produce the definitive Coverage coverage report with delta analysis after all execution cycles are complete",
        backstory=(
            "You produce the authoritative coverage report used in release sign-off. Your reports "
            "clearly show final coverage percentage, delta from initial Coverage, remaining gaps, and "
            "a clear pass/fail verdict against coverage targets."
        ),
        llm=llm,
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )


def build_sit_agent(llm: Any, tools: list) -> Agent:
    return Agent(
        role="System Integration Test Engineer",
        goal="Execute system integration tests to validate end-to-end feature behavior in the fully integrated environment",
        backstory=(
            "You are an integration testing expert who validates that new features work correctly "
            "alongside existing features. You uncover interaction bugs that unit and component tests miss."
        ),
        llm=llm,
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )


def build_nightly_integration_agent(llm: Any, tools: list) -> Agent:
    return Agent(
        role="Nightly Integration Engineer",
        goal="Integrate validated tests into nightly and regression suites for ongoing continuous execution",
        backstory=(
            "You manage test suite evolution. You ensure new tests are seamlessly integrated into "
            "continuous pipelines with proper profiles, tags, and execution configurations. "
            "Nothing enters nightly without SIT approval."
        ),
        llm=llm,
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )


def build_nightly_reporting_agent(llm: Any, tools: list) -> Agent:
    return Agent(
        role="Nightly Report Analyst",
        goal="Report on nightly run results, surface regressions, and provide trend analysis to the QA team",
        backstory=(
            "You are a data-driven analyst who monitors test health. You catch regressions early "
            "and provide trend insights that guide quality investments. Your reports are clear, "
            "actionable, and delivered to the right people."
        ),
        llm=llm,
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )


def build_qa_signoff_agent(llm: Any, tools: list) -> Agent:
    return Agent(
        role="QA Sign-off Coordinator",
        goal="Verify all release artifacts are complete and coordinate formal QA/FCS sign-off",
        backstory=(
            "You are the release quality gate. You ensure all required artifacts are present, "
            "approved, and meet quality standards before QA/FCS sign-off is granted. "
            "You coordinate approvals and record decisions with full audit trail."
        ),
        llm=llm,
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )


def build_feedback_agent(llm: Any, tools: list) -> Agent:
    return Agent(
        role="SDLC Feedback Collector",
        goal="Collect structured pipeline feedback and surface actionable improvement suggestions for the next cycle",
        backstory=(
            "You close every SDLC cycle by gathering metrics and feedback that drive continuous "
            "improvement. You analyze which stages had the most friction, where optional artifacts "
            "made the biggest difference, and what should change next time."
        ),
        llm=llm,
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )
