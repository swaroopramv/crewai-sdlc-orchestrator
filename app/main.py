"""
CrewAI SDLC Orchestrator — entry point.

Usage:
    python main.py --prd prd_001 --feature feat_user_authentication --platform CORE
    python main.py --resume pipeline_abc123
"""

import argparse
import logging
import os
import sys

from dotenv import load_dotenv
from orchestration.approval_manager import ApprovalManager
from orchestration.crew_factory import CrewFactory
from orchestration.pipeline_runner import PipelineRunner
from orchestration.retry_policy import RetryPolicy
from orchestration.state_manager import StateManager
from storage.artifact_store import ArtifactStore
from storage.checkpoint_store import CheckpointStore
from telemetry.callbacks import TelemetryCallbacks
from telemetry.metrics import MetricsCollector
from tools.approval_tools import get_approval_tools
from tools.bug_tool import bug_tools
from tools.ci_tool import ci_tools
from tools.docs_tool import get_docs_tools
from tools.notification_tool import notification_tools

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger("sdlc_orchestrator")


def build_llm(provider: str) -> object:
    """Build the chat LLM. Defaults to a local Ollama model (no API keys)."""
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=temperature,
        )
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=temperature,
        )

    # Default: local Ollama (e.g. Mistral) — fully local, no API keys required.
    from langchain_ollama import ChatOllama

    return ChatOllama(
        model=os.getenv("OLLAMA_MODEL", "mistral"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=temperature,
    )


def build_tools_registry(artifact_store: ArtifactStore, approval_manager: ApprovalManager) -> dict[str, list]:
    docs = get_docs_tools(artifact_store)
    approvals = get_approval_tools(approval_manager)
    return {
        "artifact_tools": docs,
        "docs_tool": docs,
        "ci_tool": ci_tools,
        "bug_tool": bug_tools,
        "notification_tool": notification_tools,
        "approval_tools": approvals,
    }


def build_runner(platform: str, llm_provider: str = "ollama") -> PipelineRunner:
    artifact_store = ArtifactStore(db_path=f"artifacts_{platform.lower()}.db")
    checkpoint_store = CheckpointStore(db_path=f"checkpoints_{platform.lower()}.db")

    llm = build_llm(llm_provider)

    # ApprovalManager must be created first — injected into both tools and runner
    approval_manager = ApprovalManager(
        default_timeout_hours=int(os.getenv("APPROVAL_TIMEOUT_HOURS", "24"))
    )

    tools_registry = build_tools_registry(artifact_store, approval_manager)

    crew_factory = CrewFactory(llm=llm, tools_registry=tools_registry)
    state_manager = StateManager(checkpoint_store=checkpoint_store)
    retry_policy = RetryPolicy(
        max_retries=int(os.getenv("MAX_RETRIES", "3")),
        base_delay_seconds=float(os.getenv("RETRY_DELAY_SECONDS", "30")),
    )
    metrics = MetricsCollector()
    telemetry = TelemetryCallbacks(metrics_collector=metrics)

    return PipelineRunner(
        crew_factory=crew_factory,
        state_manager=state_manager,
        retry_policy=retry_policy,
        approval_manager=approval_manager,
        artifact_store=artifact_store,
        telemetry=telemetry,
        max_triage_loops=int(os.getenv("MAX_TRIAGE_LOOPS", "5")),
    )


def main():
    parser = argparse.ArgumentParser(description="CrewAI SDLC Lifecycle Orchestrator")
    parser.add_argument("--prd-file", metavar="PATH",
                        help="Path to PRD document (.md / .txt / .json) — ingested at Stage 0")
    parser.add_argument("--prd", metavar="PRD_ID",
                        help="Existing PRD artifact ID (skips file ingestion if already in store)")
    parser.add_argument("--prd-title", metavar="TITLE",
                        help="PRD title when supplying inline text instead of a file")
    parser.add_argument("--feature", metavar="FEATURE_ID",
                        help="Existing FeatureRequest artifact ID")
    parser.add_argument("--feature-title", metavar="TITLE",
                        help="Feature title when supplying inline text instead of a file")
    parser.add_argument("--platform", choices=["CORE", "CLOUD", "EDGE"], default="CLOUD")
    parser.add_argument("--llm", choices=["ollama", "openai", "anthropic"], default="ollama")
    parser.add_argument("--resume", metavar="PIPELINE_ID", help="Resume a paused pipeline by ID")
    args = parser.parse_args()

    if not args.resume and not args.prd_file and not args.prd_title:
        parser.error("Provide --prd-file <path>, --prd-title <title>, or --prd <existing-id> to identify the PRD")

    runner = build_runner(args.platform, args.llm)

    try:
        state = runner.run(
            prd_id=args.prd or "",
            feature_id=args.feature or "",
            platform=args.platform,
            resume_pipeline_id=args.resume,
            prd_file=args.prd_file,
            prd_title=args.prd_title,
            feature_title=args.feature_title,
        )
        print(f"\nPipeline {state.pipeline_id} → {state.status}")
        summary = state.summary()
        for k, v in summary.items():
            print(f"  {k}: {v}")

    except Exception as exc:
        logger.error("Pipeline failed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
