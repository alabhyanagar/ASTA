# ASTA — Autonomous Software Testing Platform

A locally installed, user-directed software testing platform with an agent-assisted workflow. ASTA inspects a codebase or explicitly authorized running target, identifies supported checks across multiple testing domains, generates a reviewable test plan, executes approved checks in an isolated worker, evaluates results deterministically, and produces per-domain reports plus one consolidated report.

---

## Key Principles & Features

- **Local-first Architecture** — Runs on Windows via WSL2 + Docker, Linux, and macOS.
- **AI-Off by Default for Verdicts** — Pure deterministic status evaluation (`Passed`, `Failed`, `Error`, `Blocked`); AI models are bounded to recommendations and failure explanations only.
- **Multi-channel Scope Selection** — Select test categories (Unit, API, Performance, Security, etc.) via CLI flags, `asta.toml` configuration, or natural language.
- **Deterministic Planning** — Identical inputs and codebase states produce identical test plans.
- **Isolated Execution** — Deny-by-default network, CPU/memory ceilings, and read-only source code mounting.
- **Evidence-based Findings** — Every verdict links directly to execution evidence (logs, exit codes, assertion diffs).
- **Phased Interfaces** — Shared core engine powers CLI (M1), MCP Agent Server (M2), and Standalone Web/Desktop UI (M3).

---

## Quick Start

### Prerequisites
- **Windows 11** with WSL2 or native Linux / macOS
- **Docker Desktop** (for containerized execution)
- **Python 3.12+**

### Installation

```bash
# Clone the repository
git clone https://github.com/asta/asta.git
cd asta

# Activate local environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Or install in development mode
pip install -e .[dev]

# Verify installation
asta --help
```

### Typical Workflow

```bash
# 1. Register a project
asta project add /path/to/your/project

# 2. Inspect codebase profile & supported capabilities
asta inspect

# 3. Generate a deterministic test plan based on selected scope
asta plan

# 4. Review and approve checks
asta approve

# 5. Execute approved checks in the isolated worker
asta run

# 6. Check status & generate consolidated reports
asta status
asta report
```

---

## Project Structure

```
ASTA/
├── CLAUDE.md                   # Environment & CLI instructions
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Build & packaging configuration
├── TECH_STACK.md               # Definitive technology stack & architecture
├── AGENT_HANDOFF.md            # Active roadmap & handoff guide for contributors
│
├── asta/                       # SHARED APPLICATION CORE
│   ├── commands/               # CLI command handlers
│   │   ├── project_add.py
│   │   ├── inspect.py
│   │   ├── plan.py
│   │   ├── approve.py
│   │   ├── run.py
│   │   ├── status.py
│   │   ├── cancel.py
│   │   ├── rerun.py
│   │   └── report.py
│   ├── worker/                 # Execution worker & container sandbox
│   ├── models.py               # Pydantic domain models
│   ├── inspection.py           # Static project inspection
│   ├── capability.py           # Capability registry & applicability
│   ├── planner.py              # Deterministic planner
│   ├── recommendation.py       # Recommendation review & approval bindings
│   ├── language_boundary.py    # White-box vs black-box boundary checks
│   ├── persistence.py          # SQLite database storage
│   ├── state_machine.py        # Run lifecycle state machine
│   ├── audit.py                # Audit trail events
│   ├── credentials.py          # Credential injection
│   └── taxonomy.py             # Canonical check IDs & alias normalization
│
├── apps/                       # PHASED USER INTERFACES
│   ├── cli/                    # Phase 1: Local CLI runner
│   ├── mcp/                    # Phase 2: FastMCP server
│   ├── api/                    # Phase 3: FastAPI backend
│   └── web/                    # Phase 3: React / Vite frontend
│
├── tests/                      # Core test suite
└── final-docs/                 # Comprehensive documentation (PRD, TAD, SRS)
```

---

## Configuration

Create an `asta.toml` in your project root:

```toml
[project]
name = "my-project"
source = "/path/to/project"

[scope]
types = ["unit", "integration", "api"]
risk_approval = "high"

[execution]
timeout_seconds = 300
max_workers = 1

[dependencies]
pytest = ">=8.2.0,<9.0.0"
schemathesis = ">=4.0.0"

[credentials]
reference = "os-keyring:my-secret"
```

---

## CLI Command Reference

| Command | Description |
|---|---|
| `asta project add <path>` | Register a local project directory |
| `asta inspect` | Static inspection of languages, frameworks, routes, and test signals |
| `asta plan` | Generate a deterministic test plan with provenance |
| `asta approve` | Review and approve included and recommended checks |
| `asta run` | Execute approved checks in the isolated sandbox |
| `asta status` | Check status of the latest test run |
| `asta cancel` | Cancel an active run safely |
| `asta rerun` | Re-execute failed or requested checks |
| `asta report` | Generate per-domain Markdown and consolidated HTML reports |

---

## Development & Verification

```powershell
# Run the test suite (100% passing)
.\.venv\Scripts\python.exe -m pytest

# Run specific module tests
.\.venv\Scripts\python.exe -m pytest tests/test_planner.py -v

# Lint & Format
ruff check asta/
black asta/
```

---

## Current Status & Next Steps

* **M1a (Planning Foundation) — COMPLETE ✅**: Static inspection, capability evaluation, scope normalization, deterministic planning, and approval bindings are fully implemented and covered by unit/integration tests.
* **M1b (Execution Engine) — IN PROGRESS ⏳**: Building the containerized sandbox (`asta/worker/sandbox.py`), test adapters (`pytest`, `schemathesis`, `k6`), and deterministic evaluator. See [AGENT_HANDOFF.md](AGENT_HANDOFF.md) for the active implementation plan.
