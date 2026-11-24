# ASTA — Final Technology Stack & Architecture Specification

## 1. Vision & Architectural Philosophy

ASTA (Autonomous Software Testing Platform) is built with a **Shared Core Architecture** powering three sequential product phases:
1. **Phase 1 (M1):** Local CLI Tool (`asta`)
2. **Phase 2 (M2):** Model Context Protocol (MCP) Server for AI coding agents
3. **Phase 3 (M3):** Standalone Application with Web UI / Desktop Dashboard

---

## 2. Definitive Technology Stack

### A. Shared Core Engine (`core/` or `asta/core`)
- **Language & Runtime:** Python 3.12+ (fast, modern type hints, strict safety)
- **Data Modeling & Schemas:** Pydantic v2 (high-performance validation, JSON Schema export)
- **Persistence & Metadata:** SQLite (WAL mode) with SQLModel / SQLAlchemy 2.0
- **Configuration Format:** TOML (`asta.toml` / `.testagent.toml`) via `tomli` / standard library `tomllib`
- **Output Artifacts:** Versioned JSON, Markdown, and JUnit XML

### B. Phase 1: Local CLI Interface (`apps/cli` / `asta/cli.py`)
- **Framework:** `Click` / `Typer`
- **Terminal UI & Tables:** `Rich` (formatted tables for test plans, interactive checkboxes, colored status badges)
- **Packaging:** Standard Python wheel installed into virtual environment or via `pipx`

### C. Phase 2: Agent Integration (`apps/mcp`)
- **Protocol:** Model Context Protocol (MCP)
- **Framework:** `FastMCP` (Python)
- **Security Boundary:** Exposes read-only inspection, plan proposal, and execution actions. All deterministic evaluation policies and risk ceilings remain inside the Core Engine; the LLM agent cannot alter verdicts or execute outside user-approved scope.

### D. Phase 3: Web UI & Standalone Application (`apps/web` & `apps/api`)
- **Backend API:** `FastAPI` (Async REST + WebSockets for live test log streaming)
- **Frontend Framework:** `React 18+` or `Next.js` with TypeScript
- **Styling & UI Components:** `Tailwind CSS` + `shadcn/ui`
- **Desktop Packaging:** `Tauri v2` (Rust-backed lightweight container running native Webview, < 20MB installer, zero Electron bloat)

### E. Isolated Worker & Execution Sandbox
- **Primary Sandbox:** `Docker Desktop / Docker Engine` (via WSL2 on Windows, or native Linux)
- **Isolation Policy:** 
  - Read-only mount of target source code
  - Deny-by-default networking (`--network none` for static/unit/SAST; explicit allowlist for API targets)
  - Memory caps (e.g., 2GB default) and CPU throttling (e.g., 2 cores max)
- **Subprocess Fallback:** Restricted subprocess runner with process group timeouts for environments without Docker.

### F. Testing Tool Adapters
- **Functional & Unit Testing:** `pytest` (Python), `jest` / `vitest` (TypeScript/JavaScript)
- **API Contract & Fuzzing:** `schemathesis`, `httpx`
- **Performance & Load Testing:** `k6` (via CLI/container) or `locust`
- **Static Security & Code Quality:** `semgrep`, `bandit`, `trivy`

### G. Optional AI Gateway (Advisory Only)
- **Local Default:** `Ollama` running lightweight models (`qwen2.5-coder` or `llama3.2`)
- **Cloud Fallback:** `Gemini 1.5/2.0 API` / `LiteLLM`
- **Safety Rule:** AI models only suggest missing test scenarios or explain failure logs; verdicts (`Passed`, `Failed`, `Inconclusive`) are 100% computed deterministically by ASTA's evaluator.

---

## 3. Directory Layout Specification

```
ASTA/
├── CLAUDE.md                   # Environment & CLI instructions
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Build & dependency metadata
├── TECH_STACK.md               # Technology stack & architectural blueprint
│
├── asta/                       # SHARED APPLICATION CORE
│   ├── adapters/               # Tool adapters (pytest, schemathesis, k6)
│   ├── commands/               # CLI command handlers
│   ├── models.py               # Pydantic v2 domain models
│   ├── inspection.py           # Static codebase inspection engine
│   ├── capability.py           # Capability registry
│   ├── planner.py              # Deterministic test planner
│   ├── language_boundary.py    # White-box vs Black-box boundary checks
│   ├── recommendation.py       # Recommendation & approval engine
│   ├── persistence.py          # SQLite database & artifact store
│   ├── state_machine.py        # Test run state lifecycle
│   ├── audit.py                # Audit log tracking
│   ├── taxonomy.py             # Testing types & alias normalization
│   └── worker/                 # Docker container & runner sandbox
│
├── apps/                       # PHASED USER INTERFACES
│   ├── cli/                    # CLI entrypoint
│   ├── mcp/                    # MCP server implementation
│   ├── api/                    # FastAPI backend (Phase 3)
│   └── web/                    # React / Tailwind web dashboard (Phase 3)
│
├── tests/                      # Core test suite
└── final-docs/                 # Full specifications (PRD, TAD, SRS)
```
