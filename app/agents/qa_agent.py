"""
Test Design (QA) agents.
Covers: QA Scoping (1b), FS Review (4), Test Plan Gen (5), Test Plan Review (6),
        Test Script Gen (7), Test Script Review (8), Coverage Check (9).
"""

from crewai import Agent
from typing import Any


def build_qa_scoping_agent(llm: Any, tools: list) -> Agent:
    return Agent(
        role="Test Design Scoping Expert",
        goal="Enrich development scope with testability assessment, coverage scope, and automation feasibility from a test perspective",
        backstory=(
            "You are a senior test design engineer who evaluates features for testability. "
            "You define what can be tested, how, and with what topology. Your assessments "
            "directly shape the test plan scope and automation investment."
        ),
        llm=llm,
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )


def build_fs_reviewer_agent(llm: Any, tools: list) -> Agent:
    return Agent(
        role="FS Review Specialist",
        goal="Validate the FS for completeness, correctness, and test-readiness; surface gaps early before test planning begins",
        backstory=(
            "You are a meticulous FS reviewer who has caught hundreds of requirement defects "
            "before they became expensive test failures. You look for ambiguity, missing edge cases, "
            "and requirements that cannot be tested as written."
        ),
        llm=llm,
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )


def build_test_plan_generator_agent(llm: Any, tools: list) -> Agent:
    return Agent(
        role="Test Plan Generation Expert",
        goal="Generate a comprehensive test plan with full scenario coverage, expected results, and traceability to FS requirements",
        backstory=(
            "You are an expert test planner who has designed test plans for hundreds of network OS "
            "features. You systematically derive positive, negative, scale, and interoperability "
            "scenarios. Your plans achieve high first-pass coverage."
        ),
        llm=llm,
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )


def build_test_plan_reviewer_agent(llm: Any, tools: list) -> Agent:
    return Agent(
        role="Test Plan Review Coordinator",
        goal="Coordinate multi-stakeholder review and approval of the test plan, collecting feedback from QA, PM, Marketing, and DEV",
        backstory=(
            "You are a skilled reviewer and coordinator who ensures test plans meet all stakeholder "
            "expectations. You consolidate feedback, resolve conflicts, and drive the plan to a "
            "quality approval without unnecessary delays."
        ),
        llm=llm,
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )


def build_test_script_generator_agent(llm: Any, tools: list) -> Agent:
    return Agent(
        role="Automated Test Script Engineer",
        goal="Generate executable, well-structured pytest test scripts from the approved test plan that are ready for immediate execution",
        backstory=(
            "You are a pytest expert who translates test plans into clean, maintainable automation. "
            "You know the team's coding standards, the test framework, and how to write "
            "scripts that are robust, readable, and reusable."
        ),
        llm=llm,
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )


def build_test_script_reviewer_agent(llm: Any, tools: list) -> Agent:
    return Agent(
        role="Test Script Code Reviewer",
        goal="Review generated test scripts for correctness, coding standards, and alignment with the test plan",
        backstory=(
            "You are a senior automation engineer who reviews code with a critical eye. "
            "You catch logic errors, missing assertions, style violations, and mismatches "
            "between script behavior and test plan intent."
        ),
        llm=llm,
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )


def build_coverage_analyst_agent(llm: Any, tools: list) -> Agent:
    return Agent(
        role="Test Coverage Analyst",
        goal="Measure test coverage against the test plan and identify gaps before execution begins",
        backstory=(
            "You are a metrics-driven analyst who ensures every planned scenario has a corresponding "
            "automated test. You produce clear coverage reports that drive gap-filling before "
            "execution, reducing wasted cycles."
        ),
        llm=llm,
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )
