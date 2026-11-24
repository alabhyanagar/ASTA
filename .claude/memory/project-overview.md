---
name: project-overview
description: Summary of ASTA project status and direction after stakeholder approval
metadata:
  type: project
---

# ASTA Project Overview

**Status**: Stakeholder-approved (PRD v0.9, SRS v0.9, TAD v0.9 approved)  
**Baseline**: ASTA-CONTENT-BASELINE-2026-11-20-02  
**Last Updated**: 2026-11-23  

## Core Directives

### Product Vision
ASTA is a locally installed, user-directed software testing application with an agent workflow. It inspects codebases or authorized running targets, identifies supported checks, helps users select and approve testing scopes, creates reviewable test plans, generates/configures tests through adapters, executes approved checks in isolated workers, evaluates results deterministically, and produces per-domain plus consolidated reports.

### Key Principles (from PRD)
- User-directed scope: users select one or more test types; selection is multi-select
- Applicability is not authorization: system may identify checks applicable within approved scope; additional check types remain recommendations until explicitly approved
- Plan before code: present a versioned plan with expectation provenance and limits before generation/execution
- Deterministic verdicts: only user criteria, formal specifications, existing tests, configured thresholds, or defined universal checks can produce Passed/Failed
- Evidence and uncertainty: every finding cites evidence; AI hypotheses are labeled inferred with confidence or unknown
- Safe defaults: no network by default, no host secrets, no target widening, no arbitrary shell, no unbounded repair
- Honest scope: reports state included, excluded, blocked, unsupported, not applicable, not measured, and awaiting authorization checks
- One canonical check, many tags: overlapping taxonomy labels should not cause duplicate execution when target, operation, and assertion are equivalent

### Architecture Summary (from TAD 0.9)
- **Deployment**: Locally installed standalone application, CLI-first
- **Optional**: MCP integration, later UI/API
- **Technology stack**: Python 3.12.x/SQLite/Docker/Ollama — now validated and approved
- **MCP**: Interface to shared application services, not a substitute for the testing engine
- **Execution**: Deny-by-default network, explicit target authorization, one worker per machine initially
- **Isolation**: Docker proposed with adversarial isolation suite passed; trusted projects/read-only mode until boundary proof

## Major TBD Items — NOW RESOLVED (15/15)

All 15 TBD items have been resolved and recorded in `tbd-resolution-session.md`. Here's the summary:

### Critical (Must resolve before M0 entry - all 5 resolved):
1. ✅ **Python 3.12.x** with pinned dependencies (pytest 8.2.x, HTTPX 0.27.x, Schemathesis 5.6.x)
2. ✅ **WSL: Ubuntu 22.04 LTS** + **Windows 11** + **Docker Desktop 4.30.x** (ECI Business-only)
3. ✅ **CLI: `asta`** command with versioned `asta.toml` schema 1.0
4. ✅ **Numeric limits**: timeout 300s, memory 2GB, CPU 2 cores, processes 50, output 5MB, API-rate 60/min, disk 10GB
5. ✅ **Credential UX**: environment reference preferred; interactive fallback; secrets never persisted

### Important (Resolve in early M0 - all 5 resolved):
6. ✅ **SQLite schema**: SQLite + SQLAlchemy; SHA-256 content-addressed artifacts; Alembic migrations
7. ✅ **Report JSON**: Schema 1.0; ISO 8601 timestamps; 90/365-day retention policy
8. ✅ **JUnit XML**: Included in M1 with conditional mapping; validated schema
9. ✅ **Archive intake**: Included in M1; .zip/.tar/.tar.gz; 500 files, 100MB expansion, 50MB/file caps
10. ✅ **OpenAPI version**: OpenAPI 3.0 for M1; Schemathesis enabled; OpenAPI 3.1 deferred to M2

### Strategic (Resolve with stakeholder input - all 5 resolved):
11. ✅ **Security benchmarks**: 12-case adversarial isolation suite; all must pass before execution
12. ✅ **Quality thresholds**: Severity 5-level (Critical/High/Medium/Low/Informational); bug-garden 5 defects; 80% recall; flaky ≤10%; FP ≤5%
13. ✅ **Severity scale**: Critical/High/Medium/Low/Informational (mapped to risk classes)
14. ✅ **Dependency vulnerability policy**: pip-audit + OSV-Scanner; critical/high block; medium warn; LDV >90 days block
15. ✅ **Retention periods**: 90/365/730-day defaults; configurable; encrypted; automated audited cleanup

## Architectural Decisions (ADRs Recorded)

### ADR-PYTHON-VERSION — Python 3.12.x as core runtime for M1
### ADR-WSL-ENV — Ubuntu 22.04 LTS + Windows 11 + Docker Desktop 4.30.x as M1 supported environment
### ADR-CLI-COMMANDS — `asta` as CLI command; versioned `asta.toml` schema 1.0
### ADR-NUMERIC-LIMITS — timeout 300s, memory 2GB, CPU 2 cores, processes 50, output 5MB, API-rate 60/min, disk 10GB
### ADR-CREDENTIAL-UX — environment reference preferred; interactive prompt fallback; secrets never persisted
### ADR-DATA-STORAGE — SQLite + SHA-256 content-addressed artifacts for M1; migration path to PostgreSQL
### ADR-REPORT-SCHEMA — JSON report schema 1.0; ISO 8601 timestamps; 90/365-day retention
### ADR-JUNIT-XML — JUnit XML included in M1 with conditional mapping and validated schema
### ADR-ARCHIVE-INTAKE — archive intake included in M1 with extraction caps and safety checks
### ADR-OPENAPI-VERSION — OpenAPI 3.0 for M1; OpenAPI 3.1 deferred to M2
### ADR-SEC-BENCHMARK — 12-case adversarial isolation suite; minimum evidence threshold; fail-closed policy
### ADR-QUALITY-THRESHOLDS — severity scale 5-level; bug-garden 5 defects; 80% recall threshold; flaky ≤10%; FP ≤5%
### ADR-DEP-VULN — pip-audit + OSV-Scanner; critical/high block; medium warn; LDV >90 days block
### ADR-RETENTION — 90/365/730-day defaults; configurable; encrypted storage; automated cleanup; audited deletion

### Release Rule
> If the execution isolation/egress gate fails, do not ship project-code execution as enabled. Ship only a clearly labeled read-only analysis/plan/report capability if that mode independently meets its acceptance criteria; otherwise block M1 release.

## Implementation Milestones

### M0 — Design/Contract Freeze (NEXT)
**Entry Criteria** (all met now that 15 TBD items are resolved):
- ✅ All 15 TBD items resolved with owners and evidence
- ✅ All P0 backlog items have owners, estimates, and dependency reviews
- ✅ M0 decisions recorded as ADRs
- ✅ Every in-scope SRS requirement has a work item and verification artifact
- ✅ Content baseline ready for update
- ✅ Stakeholder approval recorded for PRD v0.9, SRS v0.9, TAD v0.9

**Exit Criteria** (Gate A and B pass):
- Requirements/design readiness: requirement IDs mapped; decisions recorded; approved support claims; schema and security boundaries reviewed
- Component contracts: invalid config has no side effects; adapter manifests and input/output schemas validate; approval freshness is enforced; evaluator goldens are deterministic
- Safe execution: deny-by-default network, exact target checks, read-only source, resource limits, no arbitrary commands, scoped secrets, cleanup on all exits, attack fixtures pass
- Release acceptance: full CLI journey; AI-off path; report reconciliation; restart/cancel/rerun; benchmark evidence; documented support and limitations

**Backlog Scope** (from ASTA_M1_CLI_IMPLEMENTATION_BACKLOG.md Section 9):
- ASTA-001–003, ASTA-020, ASTA-021, ASTA-040, ASTA-050, ASTA-060, ASTA-090

**Milestone**: M0 — Design/contract freeze → then transition to M1a

### M1a — Safe Skeleton
**Goal**: CLI can intake/inspect/plan/review and persist state with AI off; no test project code runs yet. Config errors and missing authority have no side effects.

### M1b — Isolated pytest Vertical Slice
**Goal**: Known Python fixture runs approved pytest in worker; produces deterministic statuses; Gate C (isolation) passes

### M1c — API Checks and Reports
**Goal**: Authorized OpenAPI API check runs through approved target policy; Markdown/JSON reports validate and redact data

### M1d — M1 Release Candidate
**Goal**: Full journey and reliability/security/compatibility evidence passes; M1 support matrix, install guide, limitations, and release claims approved

---

*This memory file captures the current state after all 15 TBD items resolved and project ready to transition to M0 design freeze.*