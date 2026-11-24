---
name: implementation-roadmap
description: Roadmap from M0 design freeze through M1 release candidate
metadata:
  type: project
---

# ASTA Implementation Roadmap

## Phase 0: M0 — Design/Contract Freeze

**Entry Criteria** (all must be met):
- All 15 TBD items resolved with owners and evidence
- All P0 backlog items have owners, estimates, and dependency reviews
- M0 decisions recorded as ADRs
- Every in-scope SRS requirement has a work item and verification artifact
- Content baseline updated to approved version
- Stakeholder approval recorded for PRD v0.9, SRS v0.9, TAD v0.9

**Exit Criteria** (Gate A and B pass):
- Requirements/design readiness: requirement IDs mapped; decisions recorded; approved support claims; schema and security boundaries reviewed
- Component contracts: invalid config has no side effects; adapter manifests and input/output schemas validate; approval freshness is enforced; evaluator goldens are deterministic
- Safe execution: deny-by-default network, exact target checks, read-only source, resource limits, no arbitrary commands, scoped secrets, cleanup on all exits, attack fixtures pass
- Release acceptance: full CLI journey; AI-off path; report reconciliation; restart/cancel/rerun; benchmark evidence; documented support and limitations

**Backlog Scope** (from ASTA_M1_CLI_IMPLEMENTATION_BACKLOG.md Section 9):
- ASTA-001–003, ASTA-020, ASTA-021, ASTA-040, ASTA-050, ASTA-060, ASTA-090

**Milestone**: M0 — Design/contract freeze

---

## Phase 1: M1a — Safe Skeleton

**Backlog Scope** (from backlog Section 5, milestone M1a):
- ASTA-010–012, ASTA-020–023, ASTA-030–032, ASTA-040–043, ASTA-050–053

**Goal**: CLI can intake/inspect/plan/review and persist state with AI off; no test project code runs yet. Config errors and missing authority have no side effects.

**Key Deliverables**:
- Supported local development setup (ASTA-010)
- Reproducible dependency and tool inventory (ASTA-011)
- Container image lifecycle and provenance (ASTA-012)
- CLI commands: project add, inspect, plan, approve (ASTA-020–022)
- Multi-channel scope input normalization (ASTA-022)
- CLI confirmation and approval interaction (ASTA-023)
- Local-folder project intake and provenance (ASTA-030)
- Safe static project inspection (ASTA-031)
- Register initial capability set and applicability states (ASTA-032)
- Versioned normalized taxonomy model (ASTA-040)
- Deterministic planner within user-approved scope (ASTA-041)
- Recommendation review and exact approval binding (ASTA-042)
- Language-boundary decision per check (ASTA-043)

**Exit Criteria**: CLI can intake/inspect/plan/review with AI off; no test execution yet

**Milestone**: M1a — Safe skeleton

---

## Phase 2: M1b — Isolated pytest Vertical Slice

**Backlog Scope** (from backlog Section 5, milestone M1b):
- ASTA-060–061, ASTA-063, ASTA-070–074, ASTA-080–081

**Goal**: A known Python fixture can run approved pytest in the worker and produce deterministic statuses; isolation Gate C passes before execution is exposed as supported.

**Key Deliverables**:
- Approve adapter manifest and output schemas (ASTA-060)
- Implement existing pytest execution adapter (ASTA-061)
- Map adapter output into canonical attempt states (ASTA-062)
- Implement disposable isolated execution worker (ASTA-070)
- Implement deny-by-default egress enforcement (ASTA-071)
- Enforce resource and output limits (ASTA-072)
- Verify worker cancellation, timeout, crash recovery, and cleanup (ASTA-073)
- Pass adversarial isolation and target-boundary acceptance suite (ASTA-074)
- Implement deterministic expectation and result evaluator (ASTA-080)
- Implement exact retry/flaky/timeout/overall verdict rules (ASTA-081)

**Exit Criteria**: Known Python fixture runs approved pytest in worker; Gate C (isolation) passes

**Milestone**: M1b — Isolated pytest vertical slice

---

## Phase 3: M1c — API Checks and Reports

**Backlog Scope** (from backlog Section 5, milestone M1c):
- ASTA-062, ASTA-071–072, ASTA-082, ASTA-090–093

**Goal**: Authorized OpenAPI API check runs through approved target policy; Markdown/JSON domain and consolidated reports validate and redact data.

**Key Deliverables**:
- Implement OpenAPI API-check adapter (ASTA-062)
- Enforce deny-by-default egress (ASTA-071)
- Enforce resource and output limits (ASTA-072)
- Approve report JSON schema and artifact contract (ASTA-090)
- Compose one report for each selected domain and one consolidated report (ASTA-091)
- Write Markdown and versioned JSON reports safely (ASTA-092)
- Add conditional JUnit XML output for pytest-compatible CI use (ASTA-093)

**Exit Criteria**: Authorized OpenAPI API check runs through approved target policy; reports validate and redact data

**Milestone**: M1c — API checks and reports

---

## Phase 4: M1d — M1 Release Candidate

**Backlog Scope** (from backlog Section 5, milestone M1d):
- ASTA-100–113

**Goal**: Full journey and reliability/security/compatibility evidence passes; M1 support matrix, install guide, limitations, and release claims approved.

**Key Deliverables**:
- Ensure complete AI-off workflow (ASTA-100)
- Add bounded local-model gateway after provider configured (ASTA-101)
- Implement natural-language selection normalization and confirmation (ASTA-102)
- Build representative Python/API bug-garden fixtures (ASTA-110)
- Run full M1 CLI acceptance journey (ASTA-111)
- Close M1 quality, security, compatibility, privacy, and license evidence (ASTA-112)
- Define release install/upgrade/uninstall and data-retention instructions (ASTA-113)

**Exit Criteria**: Full journey succeeds AI-off; M1 support matrix, install guide, limitations, and release claims approved

**Milestone**: M1d — M1 release candidate

---

## Release Gate

**Release Rule** (from backlog Section 5, item 178):
> If the execution isolation/egress gate fails, do not ship project-code execution as enabled. Ship only a clearly labeled read-only analysis/plan/report capability if that mode independently meets its acceptance criteria; otherwise block M1 release.

**Final Release Checklist**:
- M1d exit criteria met
- All quality gates passed (backlog Section 6, items 1–4)
- M1 support matrix published
- Install guide documented (WSL2 CLI installation, prerequisites, updates/rollback, state/artifact locations)
- Limitations and release claims documented
- Benchmark evidence recorded (recall, false positives, duplicates, flaky outcomes, coverage gaps, runtime)
- Numeric thresholds approved before release

---

*Roadmap created as part of project memory. Each phase depends on successful completion of previous phase exit criteria.*