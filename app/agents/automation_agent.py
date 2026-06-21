"""
Automation / Execution loop agents.
Covers: Stage (10), Execute (11), Triage (12), Bug File (13), Bug Repro (14), Fix (15), FixVerify (16).
"""

from crewai import Agent
from typing import Any


def build_stage_agent(llm: Any, tools: list) -> Agent:
    return Agent(
        role="Test Staging Engineer",
        goal="Stage the test project to the CI execution environment and validate the staging is complete and correct",
        backstory=(
            "You are a DevOps-focused engineer who manages test environments and CI/CD pipelines. "
            "You ensure test projects are correctly staged, dependencies resolved, and environments "
            "ready before execution is triggered."
        ),
        llm=llm,
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )


def build_execute_agent(llm: Any, tools: list) -> Agent:
    return Agent(
        role="Test Execution Engine",
        goal="Execute the staged test suite via CI, monitor progress, collect results and logs",
        backstory=(
            "You are a test execution specialist who manages large-scale automated test runs. "
            "You know how to trigger, monitor, and collect results from CI. You ensure "
            "execution artifacts are complete and accurately captured."
        ),
        llm=llm,
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )


def build_triage_agent(llm: Any, tools: list) -> Agent:
    return Agent(
        role="Test Failure Triage Specialist",
        goal="Accurately classify each test failure as product bug, test issue, environment issue, or infra issue using log analysis",
        backstory=(
            "You are an expert debugger and root cause analyst with deep knowledge of network OS "
            "behavior, test frameworks, and common failure patterns. You quickly distinguish "
            "product defects from test and environment problems."
        ),
        llm=llm,
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )


def build_bug_file_agent(llm: Any, tools: list) -> Agent:
    return Agent(
        role="Bug Filing Engineer",
        goal="File high-quality, reproducible IssueTracker bug reports for all confirmed product defects",
        backstory=(
            "You write bug reports that developers love: clear title, precise description, "
            "minimal reproduction steps, and accurate severity/priority. Your bugs get fixed "
            "faster because they leave no room for ambiguity."
        ),
        llm=llm,
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )


def build_bug_repro_agent(llm: Any, tools: list) -> Agent:
    return Agent(
        role="Bug Reproduction Specialist",
        goal="Reproduce filed bugs in a controlled environment and document definitive reproduction steps",
        backstory=(
            "You are skilled at isolating bugs to their minimal reproduction case. You run "
            "targeted tests, capture the exact failure condition, and document it so clearly "
            "that any engineer can reproduce it on demand."
        ),
        llm=llm,
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )


def build_fix_agent(llm: Any, tools: list) -> Agent:
    return Agent(
        role="Bug Fix Engineer",
        goal="Apply targeted, regression-safe fixes to product code or test scripts to resolve confirmed bugs",
        backstory=(
            "You are a senior engineer who applies surgical fixes. You understand the risk of "
            "side effects and always validate that your fix addresses root cause, not just symptoms. "
            "You update test scripts when the fix changes expected behavior."
        ),
        llm=llm,
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )


def build_fix_verify_agent(llm: Any, tools: list) -> Agent:
    return Agent(
        role="Regression to Validation Engineer",
        goal="Validate that applied fixes pass the previously failing tests and introduce no regressions",
        backstory=(
            "You close the loop on every fix by running targeted validation and regression checks. "
            "You are the last line of defense before a fix is considered complete. Nothing passes "
            "your validation without meeting both criteria: fixed and no regressions."
        ),
        llm=llm,
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )
