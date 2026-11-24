---
name: project-status-current
description: Current project status as of 2026-11-24 session - M1a complete, transitioning to M1b
metadata:
  type: project
  status: in-progress
  updated: 2026-11-24
---

# Project Status Current — 2026-11-24 Session

## ✅ Milestone M1a — Safe Skeleton: COMPLETE

### Implementation Status
All core M1a infrastructure implemented and tested:

| Component | File | Status |
|-----------|------|--------|
| Taxonomy & Canonical Check IDs | `asta/taxonomy.py` | ✅ Complete |
| Codebase Inspection | `asta/inspection.py` | ✅ Complete |
| Capability Registry | `asta/capability.py` | ✅ Complete |
| Deterministic Test Planner | `asta/planner.py` | ✅ Complete |
| Language Boundaries | `asta/language_boundary.py` | ✅ Complete |
| Recommendation & Approval Bindings | `asta/recommendation.py` | ✅ Complete |
| Persistence & Models | `asta/models.py`, `asta/persistence.py` | ✅ Complete |
| CLI Commands | `asta/cli.py`, `asta/commands/` | ✅ Complete |
| Audit System | `asta/audit.py` | ✅ Complete |
| State Machine | `asta/state_machine.py` | ✅ Complete |
| Scope Management | `asta/scope.py` | ✅ Complete |
| TOML Validator | `asta/toml_validator.py` | ✅ Complete |
| Schema Definitions | `asta/schema.py` | ✅ Complete |

### Test Suite Health
- **135 passed, 1 skipped** (pytest 9.2, Python 3.12)
- All capability tests: 20/20 passing
- All inspection tests: 12/12 passing
- All planner tests: passing
- All recommendation tests: passing
- All taxonomy tests: passing
- All language boundary tests: passing
- All models tests: passing

---

## 🎯 Current State: Transitioning to M1b — Worker Execution & Evaluator

### The Gap (from AGENT_HANDOFF.md)
> Currently, running `sta run` only outputs a planning summary. The `asta/worker/` directory contains only an `__init__.py` file. **Test execution has not yet been built.**

### M1b Implementation Sequence (from AGENT_HANDOFF.md)

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

### Task 1: Execution Sandboxing (`asta/worker/sandbox.py`)
- [ ] Create `BaseSandbox` abstract interface with `execute_command(cmd, timeout, env, workdir)`
- [ ] Implement `SubprocessSandbox` with timeout handling, process group termination, working directory containment, host credential scrubbing
- [ ] Implement `DockerSandbox` with read-only project mount, ephemeral scratch volume, `--network none` by default, resource limits (CPU 2 cores, memory 2048MB)

### Task 2: Standard Adapter Interface (`asta/adapters/`)
- [ ] Create `BaseAdapter`: `is_applicable(signals)`, `build_command(check, target, workspace)`, `parse_output(exit_code, stdout, stderr, artifact_path)`
- [ ] `pytest_adapter.py`: Invokes `pytest -q --tb=short --junitxml=results.xml`
- [ ] `schemathesis_adapter.py`: Runs Schemathesis API contract fuzzing against authorized endpoints

### Task 3: Worker Execution Runner (`asta/worker/runner.py`)
- [ ] `WorkerRunner` accepting `Plan`, `Project`, `BaseSandbox`
- [ ] Filters checks for `state == "included"`
- [ ] Executes each check sequentially with progress feedback
- [ ] Captures start/end time, exit code, stdout, stderr, output artifacts
- [ ] Emits `ExecutionRunResult` containing all raw attempts

### Task 4: Deterministic Evaluator (`asta/evaluator.py`)
- [ ] Pure Python evaluator (zero AI imports)
- [ ] Maps exit codes + adapter outputs to strict states: `PASSED`, `FAILED`, `ERROR`, `BLOCKED`
- [ ] Extracts failure snippets, failing test names, file/line numbers as structured evidence
- [ ] Computes overall run status

### Task 5: Wire CLI Commands & Reporting (`asta/commands/run.py`, `report.py`)
- [ ] Update `sta run`: Load approved plan/binding, initialize sandbox, execute runner, persist to SQLite
- [ ] Update `sta report`: Terminal table via `rich`, Markdown report, standalone HTML report

### Task 6: End-to-End Fixture Verification
- [ ] Build sample target in `tests/fixtures/sample_python_project` (FastAPI app with passing & failing tests)
- [ ] Write integration tests in `tests/test_execution_e2e.py` verifying full pipeline: `inspect` ➔ `plan` ➔ `approve` ➔ `run` ➔ `report`

---

## Key Files Modified in This Session

### Test Fixes (tests/)
- `tests/test_inspection.py` - Fixed to use `inspect_project()` from `asta.inspection` instead of `detect_project_profile()` from `asta.models`; added JavaScript route detection; fixed test file creation; added `json` import
- `tests/test_capability.py` - Already passing (20/20)

### Core Implementation (asta/)
- `asta/inspection.py` - Added JavaScript/TypeScript route detection in `_detect_routes()`; added pytest config detection in `_detect_frameworks()` to emit `tool` category facts
- `asta/planner.py` - Fixed `_create_plan_checks()` to work with `ApplicabilityResult` objects (not dicts); fixed `_build_canonical_check_id()` and `_get_target()` type hints; fixed `_apply_scope_filter()` and `_compute_content_hash()` for PlanCheck objects
- `asta/commands/approve.py` - Updated import from `approval` to `recommendation`

### Documentation
- `AGENT_HANDOFF.md` - Created as handoff document for AI agents
- Multiple memory files in `.claude/memory/` documenting project status, roadmap, ADRs

---

## Next Steps for M1b

**Immediate (this session or next):**
1. Create `asta/worker/sandbox.py` with `BaseSandbox`, `SubprocessSandbox`, `DockerSandbox`
2. Create `asta/adapters/` package with `BaseAdapter`, `pytest_adapter.py`
3. Create `asta/worker/runner.py` with `WorkerRunner`
4. Create `asta/evaluator.py` with deterministic evaluator
5. Update `asta/commands/run.py` and `asta/commands/report.py` to wire execution

**Validation Criteria (from backlog M1b exit):**
- Known Python fixture runs approved pytest in the worker
- Isolation Gate C passes before execution is exposed as supported
- Deterministic statuses: PASSED, FAILED, ERROR, BLOCKED, FLACKY, SKIPPED, INCONCLUSIVE, UNSUPPORTED

---

## Architecture Notes

### CLI Command Structure (from `asta/cli.py`)
```
asta
├── project
│   └── add <path>              # Create project from local folder
└── sta
    ├── inspect [path]           # Static project inspection
    ├── plan [path]              # Generate versioned test plan
    ├── approve [path]           # Review & approve checks
    ├── run [path]               # Execute approved checks (AI-off)
    ├── status                   # Show run state
    ├── cancel                   # Cancel active run
    ├── rerun [path]             # Rerun checks
    └── report                   # Generate reports from prior runs
```

### Key Invariants (from AGENT_HANDOFF.md)
1. **Deterministic Evaluator (AI-Off for Verdicts):** Only exit codes, assertions, formal schemas, and tool logs assign test statuses. An LLM is **never** permitted to declare a test passed or failed.
2. **Explicit Scope Ceiling:** The system never silently executes checks outside the user-selected and approved scope.
3. **Evidence-Linked Findings:** Every reported verdict must link to concrete execution evidence.
4. **Isolated Execution:** Tests must execute in a resource-capped, deny-by-default network sandbox.

---

*Updated: 2026-11-24 | Session: M1a complete → M1b execution engine implementation*