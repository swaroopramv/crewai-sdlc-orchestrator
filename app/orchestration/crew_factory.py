"""
CrewAI crew factory.
Builds the correct crew + task list for each stage based on platform config and LLM provider.
"""

from __future__ import annotations
from crewai import Crew, Process
from typing import Any
import yaml
from pathlib import Path

from agents.dev_agent import (
    build_dev_scoping_agent, build_fs_generator_agent, build_dev_feature_track_agent
)
from agents.qa_agent import (
    build_qa_scoping_agent, build_fs_reviewer_agent, build_test_plan_generator_agent,
    build_test_plan_reviewer_agent, build_test_script_generator_agent,
    build_test_script_reviewer_agent, build_coverage_analyst_agent,
)
from agents.automation_agent import (
    build_stage_agent, build_execute_agent, build_triage_agent, build_bug_file_agent,
    build_bug_repro_agent, build_fix_agent, build_fix_verify_agent,
)
from agents.release_agent import (
    build_support_kt_agent, build_docs_agent, build_coverage_final_agent, build_sit_agent,
    build_nightly_integration_agent, build_nightly_reporting_agent,
    build_qa_signoff_agent, build_feedback_agent,
)

CONFIG_DIR = Path(__file__).parent.parent / "config"


def _load_yaml(filename: str) -> dict:
    with open(CONFIG_DIR / filename) as f:
        return yaml.safe_load(f)


class CrewFactory:
    """Builds single-stage Crew instances on demand."""

    def __init__(self, llm: Any, tools_registry: dict[str, list]):
        self.llm = llm
        self.tools = tools_registry
        self._agents_config = _load_yaml("agents.yaml")["agents"]
        self._platforms_config = _load_yaml("platforms.yaml")["platforms"]

    def _tools_for(self, agent_key: str) -> list:
        cfg = self._agents_config.get(agent_key, {})
        tool_names = cfg.get("tools", [])
        result = []
        for name in tool_names:
            result.extend(self.tools.get(name, []))
        return result

    # ------------------------------------------------------------------
    # Phase 1
    # ------------------------------------------------------------------
    def dev_scoping_crew(self, task) -> Crew:
        agent = build_dev_scoping_agent(self.llm, self._tools_for("dev_scoping"))
        task.agent = agent
        return Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)

    def qa_scoping_crew(self, task) -> Crew:
        agent = build_qa_scoping_agent(self.llm, self._tools_for("qa_scoping"))
        task.agent = agent
        return Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)

    def fs_gen_crew(self, task) -> Crew:
        agent = build_fs_generator_agent(self.llm, self._tools_for("fs_generator"))
        task.agent = agent
        return Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)

    def dev_track_crew(self, task) -> Crew:
        agent = build_dev_feature_track_agent(self.llm, self._tools_for("dev_feature_track"))
        task.agent = agent
        return Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)

    # ------------------------------------------------------------------
    # Phase 2
    # ------------------------------------------------------------------
    def fs_review_crew(self, task) -> Crew:
        agent = build_fs_reviewer_agent(self.llm, self._tools_for("fs_reviewer"))
        task.agent = agent
        return Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)

    def test_plan_gen_crew(self, task) -> Crew:
        agent = build_test_plan_generator_agent(self.llm, self._tools_for("test_plan_generator"))
        task.agent = agent
        return Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)

    def test_plan_review_crew(self, task) -> Crew:
        agent = build_test_plan_reviewer_agent(self.llm, self._tools_for("test_plan_reviewer"))
        task.agent = agent
        return Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)

    # ------------------------------------------------------------------
    # Phase 3
    # ------------------------------------------------------------------
    def test_script_gen_crew(self, task) -> Crew:
        agent = build_test_script_generator_agent(self.llm, self._tools_for("test_script_generator"))
        task.agent = agent
        return Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)

    def test_script_review_crew(self, task) -> Crew:
        agent = build_test_script_reviewer_agent(self.llm, self._tools_for("test_script_reviewer"))
        task.agent = agent
        return Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)

    def coverage_check_crew(self, task) -> Crew:
        agent = build_coverage_analyst_agent(self.llm, self._tools_for("coverage_analyst"))
        task.agent = agent
        return Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)

    # ------------------------------------------------------------------
    # Phase 4
    # ------------------------------------------------------------------
    def stage_crew(self, task) -> Crew:
        agent = build_stage_agent(self.llm, self._tools_for("stage_agent"))
        task.agent = agent
        return Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)

    def execute_crew(self, task) -> Crew:
        agent = build_execute_agent(self.llm, self._tools_for("execute_agent"))
        task.agent = agent
        return Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)

    def triage_crew(self, task) -> Crew:
        agent = build_triage_agent(self.llm, self._tools_for("triage_agent"))
        task.agent = agent
        return Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)

    def bug_file_crew(self, task) -> Crew:
        agent = build_bug_file_agent(self.llm, self._tools_for("bug_file_agent"))
        task.agent = agent
        return Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)

    def bug_repro_crew(self, task) -> Crew:
        agent = build_bug_repro_agent(self.llm, self._tools_for("bug_repro_agent"))
        task.agent = agent
        return Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)

    def fix_crew(self, task) -> Crew:
        agent = build_fix_agent(self.llm, self._tools_for("fix_agent"))
        task.agent = agent
        return Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)

    def fix_verify_crew(self, task) -> Crew:
        agent = build_fix_verify_agent(self.llm, self._tools_for("fix_verify_agent"))
        task.agent = agent
        return Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)

    # ------------------------------------------------------------------
    # Phase 5
    # ------------------------------------------------------------------
    def support_kt_crew(self, task) -> Crew:
        agent = build_support_kt_agent(self.llm, self._tools_for("support_kt_agent"))
        task.agent = agent
        return Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)

    def docs_crew(self, task) -> Crew:
        agent = build_docs_agent(self.llm, self._tools_for("docs_agent"))
        task.agent = agent
        return Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)

    def coverage_final_crew(self, task) -> Crew:
        agent = build_coverage_final_agent(self.llm, self._tools_for("coverage_final_agent"))
        task.agent = agent
        return Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)

    def sit_crew(self, task) -> Crew:
        agent = build_sit_agent(self.llm, self._tools_for("sit_agent"))
        task.agent = agent
        return Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)

    def nightly_integration_crew(self, task) -> Crew:
        agent = build_nightly_integration_agent(self.llm, self._tools_for("nightly_integration_agent"))
        task.agent = agent
        return Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)

    def nightly_reporting_crew(self, task) -> Crew:
        agent = build_nightly_reporting_agent(self.llm, self._tools_for("nightly_reporting_agent"))
        task.agent = agent
        return Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)

    def qa_signoff_crew(self, task) -> Crew:
        agent = build_qa_signoff_agent(self.llm, self._tools_for("qa_signoff_agent"))
        task.agent = agent
        return Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)

    def feedback_crew(self, task) -> Crew:
        agent = build_feedback_agent(self.llm, self._tools_for("feedback_agent"))
        task.agent = agent
        return Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
