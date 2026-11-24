# AGENT_HANDOFF.md — ASTA Implementation Status & Execution Plan

> **Note for AI Agents & Contributors:**  
> Read this document first before making changes. It provides a real-time status of the codebase, architectural invariants, completed tasks, and the step-by-step implementation plan for the active milestone.

---

## 1. Project Mission & Invariants

ASTA (Autonomous Software Testing Platform) is a locally installed, user-directed testing platform. Users provide a codebase, select test domains (Unit, Integration, API, Load, Security, etc.), review a deterministic test plan, approve it, and ASTA executes the tests in an isolated worker, compiling an evidence-backed consolidated report.

### Non-Negotiable Core Invariants:
1. **Deterministic Evaluator (AI-Off for Verdicts):** Only exit codes, assertions, formal schemas, and tool logs assign test statuses (`Passed`, `Failed`, `Error`, `Blocked`). An LLM is **never** permitted to declare a test passed or failed.
2. **Explicit Scope Ceiling:** The system never silently executes checks outside the user-selected and approved scope. Unselected checks remain recommendations until explicitly approved.
3. **Evidence-Linked Findings:** Every reported verdict must link to concrete execution evidence (stdout/stderr, stack trace, HTTP response, line number).
4. **Isolated Execution:** Tests must execute in a resource-capped, deny-by-default network sandbox (Docker primary, restricted subprocess fallback).

---

## 2. Current Project State & What Has Been Done

### Milestone Status: **Transitioning from M1a (Planning Foundation) to M1b (Execution Engine)**

#### Completed Items:
* **Taxonomy & Canonical Check IDs (`asta/taxonomy.py`):** Multi-dimensional mapping for test levels, domains, techniques, and intents with multi-channel alias deduplication.
* **Codebase Inspection (`asta/inspection.py`):** Static analyzer for language detection, frameworks, manifests, routes, and test files without running untrusted project code.
* **Capability Registry (`asta/capability.py`):** Adapter definitions, required signals, prerequisites, and applicability evaluation (`ApplicabilityResult`).
* **Deterministic Test Planner (`asta/planner.py`):** Identical inputs produce identical, versioned plans with provenance hashing and material change detection.
* **Language Boundaries (`asta/language_boundary.py`):** Enforces white-box (in-language) vs black-box (API/service) boundary rules.
* **Recommendation & Approval Bindings (`asta/recommendation.py`):** Recommendation generation for out-of-scope capabilities, user review decisions, and cryptographic approval bindings.
* **Persistence & Models (`asta/models.py`, `asta/persistence.py`):** Project profiles, configurations, and SQLite database storage.
* **Architecture & Backlog (`final-docs/`, `TECH_STACK.md`):** Complete PRD, TAD, SRS, and phased tech stack (CLI ➔ MCP ➔ Web/Desktop UI).
* **Test Suite Health:** **100% Passing** (`135 passed, 1 skipped` on pytest 9.2 with Python 3.12).

---

## 3. Immediate Gap (Why the Work is Blocked on Execution)

Currently, running `sta run` only outputs a planning summary. The `asta/worker/` directory contains only an `__init__.py` file. **Test execution has not yet been built.**

---

## 4. Active Task: Milestone 1b — Worker Execution & Evaluator

We are currently building the **Isolated Execution Engine & Deterministic Evaluator** so ASTA can execute approved test plans and generate reports.

### Detailed Implementation Sequence:

```
[Approved Plan] 
       │
       ▼
1. asta/worker/sandbox.py  (Docker / Subprocess Isolation)
       │
       ▼
2. asta/adapters/          (PytestAdapter, SchemathesisAdapter, k6Adapter)
       │
       ▼
3. asta/worker/runner.py   (Execution Coordinator & Evidence Collector)
       │
       ▼
4. asta/evaluator.py       (Deterministic Status & Verdict Assignment)
       │
       ▼
5. asta/commands/run.py & report.py (CLI User Journey + HTML/MD Reports)
```

---

### Step-by-Step Task Breakdown:

#### Task 1: Execution Sandboxing (`asta/worker/sandbox.py`)
* Create `BaseSandbox` abstract interface with `execute_command(cmd, timeout, env, workdir)`.
* Implement `SubprocessSandbox`:
  - Enforce timeout handling with process group termination (`SIGKILL`/`taskkill`).
  - Strict working directory containment.
  - Scrub host credentials from environment variables (`credentials.py`).
* Implement `DockerSandbox`:
  - Mount project directory as read-only volume (`:ro`).
  - Ephemeral scratch volume for test outputs.
  - `--network none` by default; explicit allowlist if network target authorized.
  - Resource limits: CPU limit (default 2 cores), memory limit (default 2048MB).

#### Task 2: Standard Adapter Interface (`asta/adapters/`)
Create standardized adapters inheriting from `BaseAdapter`:
* `BaseAdapter`:
  - `is_applicable(signals) -> bool`
  - `build_command(check, target, workspace) -> List[str]`
  - `parse_output(exit_code, stdout, stderr, artifact_path) -> RawEvidence`
* **`pytest_adapter.py`**: Invokes `pytest -q --tb=short --junitxml=results.xml`.
* **`schemathesis_adapter.py`**: Runs Schemathesis API contract fuzzing against authorized endpoints.

#### Task 3: Worker Execution Runner (`asta/worker/runner.py`)
* Export `WorkerRunner`:
  - Accepts `plan: Plan`, `project: Project`, `sandbox: BaseSandbox`.
  - Filters checks for `state == "included"`.
  - Executes each check sequentially with progress feedback.
  - Captures start time, end time, exit code, stdout, stderr, and output artifacts.
  - Emits `ExecutionRunResult` containing all raw attempts.

#### Task 4: Deterministic Evaluator (`asta/evaluator.py`)
* Implement pure Python evaluator (zero AI imports):
  - Maps exit codes + adapter outputs to strict states: `PASSED`, `FAILED`, `ERROR`, `BLOCKED`.
  - Extracts failure snippets, failing test names, and file/line numbers as structured evidence.
  - Computes overall run status:
    - If any check fails ➔ Run verdict `FAILED`.
    - If all pass ➔ Run verdict `PASSED`.
    - If prerequisites missing ➔ `BLOCKED`.

#### Task 5: Wire CLI Commands & Reporting (`asta/commands/run.py`, `report.py`)
* Update `sta run`:
  - Load latest approved plan & binding.
  - Initialize sandbox (Docker if available, fallback to Subprocess).
  - Execute runner and persist execution evidence to SQLite (`persistence.py`).
* Update `sta report`:
  - Generate human-readable terminal table via `rich`.
  - Export structured Markdown report (`reports/asta_report_<id>.md`).
  - Export standalone HTML report with per-domain breakdown.

#### Task 6: End-to-End Fixture Verification
* Build sample target in `tests/fixtures/sample_python_project` (FastAPI app with passing & failing tests).
* Write integration tests in `tests/test_execution_e2e.py` verifying full pipeline:
  `inspect` ➔ `plan` ➔ `approve` ➔ `run` ➔ `report`.

---

## 5. Development & Testing Commands

Always run Python commands using the virtual environment:
```powershell
# Run full test suite
.\.venv\Scripts\python.exe -m pytest

# Run specific test file
.\.venv\Scripts\python.exe -m pytest tests/test_planner.py -v

# Run ASTA CLI
.\.venv\Scripts\python.exe -m asta.cli --help
```
