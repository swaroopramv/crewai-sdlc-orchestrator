# CrewAI SDLC Orchestrator

End-to-End Agentic Test SDLC Lifecycle Orchestrator built on [CrewAI](https://docs.crewai.com).

Orchestrates **24 stages** across **5 phases** — from feature scoping to QA sign-off — using specialized AI agents with full artifact traceability, checkpoint-based resume, and human-in-the-loop approvals.

Runs **100% locally** by default using [Ollama](https://ollama.com) + **Mistral** (no API keys, no cloud), with optional OpenAI/Anthropic providers.

---

## Project Structure

```
crewai-sdlc-orchestrator/
├── app/
│   ├── main.py                  # Entry point / CLI
│   ├── config/
│   │   ├── platforms.yaml       # CORE / CLOUD / EDGE platform configs + available agents
│   │   ├── agents.yaml          # Agent roles, goals, backstories, ownership
│   │   └── pipeline.yaml        # Stage definitions, approval gates, triage loop
│   ├── agents/
│   │   ├── dev_agent.py          # DEV agents: Scoping(1a), FS Gen(2), Dev Track(3)
│   │   ├── qa_agent.py          # QA agents: Scoping(1b), FS Review(4), TP Gen(5), TP Review(6), TS Gen(7), TS Review(8), Coverage(9)
│   │   ├── automation_agent.py  # Stage(10), Execute(11), Triage(12), Bug(13-14), Fix(15), FixVerify(16)
│   │   └── release_agent.py     # Support KT(17), Docs(18), Coverage Final(19), SIT(20), Nightly(21-22), QA(23), Feedback(24)
│   ├── tasks/
│   │   ├── scoping.py           # Stage 1a, 1b tasks
│   │   ├── fs.py               # Stage 2, 3, 4 tasks
│   │   ├── test_plan.py         # Stage 5, 6 tasks
│   │   ├── test_scripts.py      # Stage 7, 8, 9 tasks
│   │   ├── execution.py         # Stage 10, 11 tasks
│   │   ├── triage.py            # Stage 12-16 (triage loop) tasks
│   │   └── release.py           # Stage 17-24 tasks
│   ├── models/
│   │   ├── artifacts.py         # Pydantic models for all 24+ artifact types
│   │   ├── pipeline_state.py    # PipelineState, StageRun, status enums
│   │   ├── approvals.py         # ApprovalRequest, ApprovalDecision
│   │   └── telemetry.py         # TelemetryEvent, StageMetrics, PipelineMetrics
│   ├── orchestration/
│   │   ├── crew_factory.py      # Creates per-stage CrewAI Crew instances
│   │   ├── pipeline_runner.py   # Main pipeline execution with triage loop
│   │   ├── state_manager.py     # Wraps PipelineState + CheckpointStore
│   │   ├── approval_manager.py  # Human approval request lifecycle
│   │   └── retry_policy.py      # Configurable retry with exponential backoff
│   ├── tools/
│   │   ├── ci_tool.py        # CI staging + execution tools
│   │   ├── bug_tool.py          # IssueTracker bug filing + update tools
│   │   ├── docs_tool.py         # Artifact read/write tools
│   │   └── notification_tool.py # Chat, email, approval notification tools
│   ├── storage/
│   │   ├── artifact_store.py    # SQLite artifact persistence (swap to Postgres/S3)
│   │   └── checkpoint_store.py  # SQLite checkpoint persistence for resume
│   └── telemetry/
│       ├── callbacks.py         # Pipeline/stage lifecycle event emitter
│       └── metrics.py           # Metrics aggregation from events
└── tests/
    └── unit/
        ├── test_models.py       # Artifact + state model tests
        ├── test_retry_policy.py # Retry policy behavior tests
        └── test_storage.py      # Artifact + checkpoint store tests
```

---

## Pipeline Phases

| Phase | Stages | Ownership |
|-------|--------|-----------|
| 1 — Scope & Development | 1a DEV Scope → 1b QA Scope → 2 FS Gen → 3 Dev Track | DEV + QA |
| 2 — Review & Plan | 4 FS Review → 5 TP Gen → 6 TP Review ✅ | QA + Co-owned |
| 3 — Automate & Review | 7 TS Gen → 8 TS Review → 9 Coverage Check | QA |
| 4 — Execute & Triage Loop | 10 Stage → 11 Execute → 12 Triage → 13 Bug File → 14 Bug Repro → 15 Fix ✅ → 16 FixVerify | QA + Co-owned |
| 5 — Release | 17 Support KT → 18 Docs → 19 Coverage Final → 20 SIT → 21 Nightly → 22 Reporting → 23 QA Sign-off ✅ → 24 Feedback | QA |

✅ = Human approval gate

---

## Setup

### 1. Install the local LLM (Ollama + Mistral)

```bash
# Install Ollama from https://ollama.com, then pull the model
ollama pull mistral
```

### 2. Install dependencies

```bash
poetry install
```

### 3. Configure environment

```bash
cp .env.example .env
# Defaults to local Ollama — no API keys needed.
# (Optionally add OpenAI/Anthropic keys to use a cloud provider.)
```

### 4. Run the pipeline

```bash
# Start a new pipeline (local Ollama/Mistral by default)
python app/main.py --prd prd_001 --feature feat_user_login --platform CLOUD

# Resume a paused pipeline
python app/main.py --resume pipeline_abc123

# Use a cloud provider instead of local Ollama
python app/main.py --prd prd_001 --feature feat_001 --platform CORE --llm anthropic
```

---

## Key Design Decisions

### Provider-Agnostic (local-first)
Defaults to a local **Ollama** model (Mistral) so it runs with no API keys or cloud cost. The LLM provider is configured via the `--llm` flag (`ollama` / `openai` / `anthropic`) or `LLM_PROVIDER` env var. Adding a new provider requires only a new `build_llm()` branch in `main.py`.

### Artifact Data Contracts
Every artifact is a Pydantic model. Stages produce typed outputs stored in `ArtifactStore`. Downstream stages reference upstream artifacts by ID — never by in-memory references.

### Checkpoint & Resume
`CheckpointStore` persists `PipelineState` after every stage. `--resume PIPELINE_ID` loads the latest checkpoint and skips all completed stages.

### Triage Loop
Phase 4 runs a configurable loop (max `MAX_TRIAGE_LOOPS`). The loop exits when the triage report contains zero product bugs, or when the loop limit is reached.

### Human-in-the-Loop
Stages with `human_input=True` in their CrewAI task pause for human input. `ApprovalManager` tracks approval requests and decisions with full audit trail.

### Platform-Specific Agents
`platforms.yaml` defines which stages and tools are available per platform (CORE/CLOUD/EDGE). `CrewFactory` respects this when building crews.

---

## Running Tests

```bash
poetry run pytest
# With coverage
poetry run pytest --cov=app --cov-report=html
```

---

## Adding a New Stage

1. Add the stage definition to `config/pipeline.yaml`
2. Add the agent config to `config/agents.yaml`
3. Create the task function in the appropriate `tasks/` file
4. Create the agent builder in the appropriate `agents/` file
5. Add a crew builder method to `orchestration/crew_factory.py`
6. Call the new crew in `orchestration/pipeline_runner.py`
