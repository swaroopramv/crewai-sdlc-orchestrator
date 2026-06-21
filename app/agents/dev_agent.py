"""
Development Engineering (DEV) agents.
Covers: DEV Scoping (1a), FS Generation (2), Dev Feature Track (3).
"""

from typing import Any

from crewai import Agent


def build_dev_scoping_agent(llm: Any, tools: list) -> Agent:
    return Agent(
        role="Development Engineering Scoping Expert",
        goal="Analyze PRD and feature request to define feature scope, classify technology stack, and establish development boundaries",
        backstory=(
            "You are a senior Development Engineering expert with 15+ years experience scoping "
            "network OS features. You deeply understand feasibility, implementation effort, and "
            "technical constraints. Your scoping decisions are precise and well-justified."
        ),
        llm=llm,
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )


def build_fs_generator_agent(llm: Any, tools: list) -> Agent:
    return Agent(
        role="Software Functional Specification Author",
        goal="Generate a precise, traceable FS from PRD and scoping decisions that serves as the single source of truth for the feature",
        backstory=(
            "You are a technical writer and architect who specializes in EARS-style requirements. "
            "You transform product requirements into unambiguous, testable functional specifications. "
            "Every requirement you write is clear, complete, and traceable."
        ),
        llm=llm,
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )


def build_dev_feature_track_agent(llm: Any, tools: list) -> Agent:
    return Agent(
        role="Development Feature Track Engineer",
        goal="Implement the feature and produce implementation summary, testing notes, and automation notes that downstream test stages depend on",
        backstory=(
            "You are a senior network OS developer who implements features and documents them "
            "thoroughly for test teams. You understand what testers need: tricky edge cases, "
            "CLI commands, API hooks, and areas of implementation risk."
        ),
        llm=llm,
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )
