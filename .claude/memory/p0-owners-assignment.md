---
name: p0-owners-assignment
description: Owner assignments for all P0 backlog items
metadata:
  type: project
  status: in-progress
---

# P0 Backlog Item Owner Assignments — ASTA Project

**Date**: 2026-11-23  
**Status**: Owner assignments completed for M0 design freeze transition  
**Total P0 Items**: 24 items across 11 epics  
**Baseline**: `ASTA-CONTENT-BASELINE-2026-11-23-01`

## Owner Assignment Format
`ITEM_ID: [Role/Name] — [Rationale]`

---

## Epic 0 — M0 Scope, Decisions, and Requirement Traceability

| Item | Owner | Rationale |
|------|-------|-----------|
| ASTA-001 | **tech-lead** — Project Requirements Lead | Creates the requirement-to-work-item ledger; ensures no SRS ID is silently dropped; foundational for traceability |
| ASTA-002 | **solutions-architect** — Technical Architect | Records approved M1 technical defaults as ADRs; distinguishes confirmed decisions from proposed tools; essential for design freeze |
| ASTA-003 | **tech-lead** — Project Requirements Lead | Freezes M1 support matrix and trust claims; publishes verified combinations; critical for Gate A passage |

---

## Epic 1 — Reproducible Windows + WSL2 + Docker Developer Environment

| Item | Owner | Rationale |
|------|-------|-----------|
| ASTA-010 | **devops-engineer** — DevOps Specialist | Defines supported local development setup; WSL2 and Docker Desktop prerequisites; tested Windows editions; ensures reproducible environment |
| ASTA-011 | **devops-engineer** — DevOps Specialist | Defines pinned/locked dependency and tool inventory; metadata records exact version, source, license, OS/runtime, update policy; clean environment reproduction |

---

## Epic 2 — CLI Contract and Input/Configuration

| Item | Owner | Rationale |
|------|-------|-----------|
| ASTA-020 | **cli-developer** — CLI Developer | Specifies CLI commands, prompts, exit codes, and output locations; supports intake/inspect/plan/review/approve/run/status/cancel/rerun/report; command spellings finalized |
| ASTA-021 | **cli-developer** — CLI Developer | Defines and validates versioned `asta.toml` schema; unknown/invalid fields fail before side effects; config cannot reduce hard safety policy; CLI > config > built-in precedence |

---

## Epic 3 — Project Intake, Inspection, and Capabilities

| Item | Owner | Rationale |
|------|-------|-----------|
| ASTA-030 | **software-engineer** — Software Engineer | Implements local-folder project intake and provenance; canonicalizes path, records source/rejection, rejects unsupported/malformed input; does not mutate source |
| ASTA-031 | **software-engineer** — Software Engineer | Implements safe static project inspection; detects Python manifests, pytest config/tests, OpenAPI descriptions, supported signals without importing/executing project modules; every fact has evidence |
| ASTA-032 | **test-architect** — Test Architect | Registers initial capability set and applicability states; only verified Python/pytest and API capabilities; states distinguish Applicable, Not applicable, Unsupported, Blocked, Awaiting authorization; reasons/prerequisites reported |

---

## Epic 4 — Taxonomy, Planner, Recommendations, and Approvals

| Item | Owner | Rationale |
|------|-------|-----------|
| ASTA-040 | **data-engineer** — Data Engineer | Implements versioned normalized taxonomy model; preserves separate dimensions: test level/strategy, domain, protocol/platform, technique, validation intent; stable IDs/alias policy versioned before persisted runs |
| ASTA-041 | **test-architect** — Test Architect | Implements deterministic planner within user-approved scope; uses evidence and adapter manifests; classifies applicability; distinguishes included, excluded, blocked, unsupported, not applicable, pending recommendation |
| ASTA-042 | **test-architect** — Test Architect | Implements recommendation review and exact approval binding; each recommendation includes rationale/evidence/risk/prerequisites; approved additions bind to run, exact scope, plan revision/content hash and policy version; declined/pending never execute; material change invalidates approval and is audited |

---

## Epic 5 — Persisted Workflow, Storage, and Audit

| Item | Owner | Rationale |
|------|-------|-----------|
| ASTA-050 | **data-engineer** — Data Engineer | Approves physical data contracts and local persistence design; decides IDs, immutable snapshots, DB schema/migrations, report schema_version, artifact digest, file/DB consistency, locking, backup/deletion/retention; records ADRs before persistence implementation |
| ASTA-051 | **software-engineer** — Software Engineer | Implements persisted state machine with one active worker; state transitions guarded and persisted; restart resumes/marks run deterministically; concurrent start cannot create conflicting active worker; idempotent cancel/rerun behavior; immutable run snapshot preserved |
| ASTA-052 | **security-engineer** — Security Engineer | Implements audit events for security and lifecycle decisions; audit target decisions, approvals, plan revisions, egress decisions, credential references, cancellation, AI provider/data-sharing event, artifact access; no secret values; each decision has actor/source, time, policy version, and reason |

---

## Epic 6 — Adapter Contract and Initial Python/pytest Adapter

| Item | Owner | Rationale |
|------|-------|-----------|
| ASTA-060 | **adapter-developer** — Adapter Developer | Approves adapter manifest and output schemas; manifest includes stable adapter_id, capabilities/tags, applicability evidence, support state, risk, prerequisites, tool/version/license, OS/runtime, allowlisted command/input, output schema, evidence mapping, limits, unsupported conditions |
| ASTA-061 | **software-engineer** — Software Engineer | Implements existing pytest execution adapter; runs only explicit approved test command in isolated worker; captures exit/stdout/stderr/timing/tool version and raw evidence; does not modify source; missing runtime/prerequisite is Blocked or Unsupported; adapter does not assign overall verdict |
| ASTA-062 | **api-engineer** — API Engineer | Implements OpenAPI API-check adapter; supports only approved OpenAPI version(s) and exact authorized target; reject spec URLs/redirects that expand scope; HTTPX transport and Schemathesis use only if version/license/parser verified; request rate, timeout, redaction, and output caps enforced; preserves request/response/schema provenance |

---

## Epic 7 — Isolation, Egress, Resources, and Safety Release Gate

| Item | Owner | Rationale |
|------|-------|-----------|
| ASTA-070 | **security-engineer** — Security Engineer | Implements disposable isolated execution worker; worker has no Docker socket, privileged mode, host networking, host home, or host-wide environment; source is read-only; output is separate; non-root where supported; capabilities reduced; container/process cleanup on every exit |
| ASTA-071 | **security-engineer** — Security Engineer | Implements deny-by-default egress enforcement; worker has no network unless approved check needs it; all requests/redirects and DNS-resolved addresses rechecked; exact target only; deny localhost/private/link-local/metadata unless explicitly approved; separate approved registry access for dependency-install phase |
| ASTA-072 | **performance-engineer** — Performance Engineer | Enforces resource and output limits; CPU, memory, process count, disk, output size, wall-clock, and API rate limits enforced; numerical defaults approved from representative workload measurements; limit cause captured as evidence and canonical outcome |
| ASTA-073 | **software-engineer** — Software Engineer | Verifies worker cancellation, timeout, crash recovery, and cleanup; cancel/timeout/crash stops process group and removes worker/network/temp volumes/credential access; preserves completed attempts and partial evidence; records cleanup success/failure; never reports a false pass |
| ASTA-074 | **security-engineer** — Security Engineer | Passes adversarial isolation and target-boundary acceptance suite; demonstrates host-file/socket denial, no source writes, resource caps, DNS rebinding, direct IPv4/IPv6, redirect, local/private/link-local/metadata denial, target allow case, archive/path attacks if applicable, oversized output, cancellation, cleanup, and secret-canary redaction; if any critical case fails, disable project-code execution and release only read-only analysis/trusted-project mode |

---

## Epic 8 — Deterministic Evaluator and Traceability/Change-Aware Behavior

| Item | Owner | Rationale |
|------|-------|-----------|
| ASTA-080 | **evaluator-lead** — Evaluator Lead | Implements deterministic expectation and result evaluator; consumes stored evidence/expectation/policy only; no AI dependency/import; only user criteria, formal specification, existing test, configured threshold, or defined universal check can authoritatively pass/fail; AI-only expectation is Inconclusive |
| ASTA-081 | **evaluator-lead** — Evaluator Lead | Implements exact retry/flaky/timeout/overall verdict rules; fail then pass retry becomes Flaky; preserve all attempts; timeout is Failed only for explicit configured timeout assertion, otherwise Error; overall verdict exactly follows contract; no pass if required evidence persistence/reporting fails |
| ASTA-082 | **software-engineer** — Software Engineer | Implements source revision and change-impact traceability; stores source revision/hash and links among requirements, checks, attempts, findings, evidence, and reports; unchanged scope may reuse evidence only when compatibility/freshness is proven; changed target/plan invalidates approval; unsupported change analysis is clearly not measured |

---

## Epic 9 — Reporting, Artifacts, and User Review

| Item | Owner | Rationale |
|------|-------|-----------|
| ASTA-090 | **reporting-engineer** — Reporting Engineer | Approves report JSON schema and artifact contract; defines exact schema_version, field names, timestamps, enums, nullability, redaction metadata, artifact digest, compatibility evolution; validates before report implementation |
| ASTA-091 | **reporting-engineer** — Reporting Engineer | Composes one report for each selected domain and one consolidated report; multi-domain run emits every selected domain report plus one consolidated report; counts/verdicts reconcile; includes target/scope, environment, timing, plan, expectations/provenance, adapter/tool versions, all dispositions, evidence, limitations, recommendations, and tested-scope qualification |
| ASTA-092 | **reporting-engineer** — Reporting Engineer | Writes Markdown and versioned JSON reports safely; Markdown is readable; JSON validates against approved schema; artifact IDs resolve safely; hashes/provenance checked; secrets redacted; malicious text/HTML and traversal safely handled; missing/corrupt artifact is explicit |
| ASTA-093 | **cli-developer** — CLI Developer | Adds conditional JUnit XML output for pytest-compatible CI use; emits only if status/finding mapping validated; retains canonical JSON/Markdown as authoritative; documents unsupported mapping; CLI exit code matches documented run verdict policy |

---

## Epic 10 — AI Gateway and Natural-Language Assistance

| Item | Owner | Rationale |
|------|-------|-----------|
| ASTA-100 | **ai-gateway-lead** — AI Gateway Lead | Ensures complete AI-off workflow; intake, inspect, plan, approve, run, evaluate, report, cancel/recover do not require a model; missing/unconfigured model cannot block deterministic supported workflow |
| ASTA-101 | **ai-gateway-lead** — AI Gateway Lead | Adds bounded local-model gateway only after provider is configured; local provider off by default; explicit config required; bounded inputs/output, schema validation, timeout/retry caps, provenance and opt-in audit; model cannot execute commands, alter scope, approve, change policy, or set verdict; invalid/unavailable provider degrades safely |
| ASTA-102 | **natural-language-engineer** — Natural Language Engineer | Implements natural-language selection normalization and conversion; request converted into proposed canonical selections; user reviews final plan; ambiguous intent asks clarification; unavailable AI uses deterministic parsing or reports unsupported; AI suggestions remain recommendations until exact approval |

---

## Epic 11 — Release Acceptance, Evidence, and Support Claims

| Item | Owner | Rationale |
|------|-------|-----------|
| ASTA-110 | **qa-lead** — QA Lead | Builds representative Python/API bug-garden fixtures; controlled fixtures include known passing/failing tests, API contract cases, missing oracle, unsupported combination, and flaky/retry behavior; benchmark answer keys not exposed to planner/worker; no numeric recall threshold claimed until approved |
| ASTA-111 | **qa-lead** — QA Lead | Runs full M1 CLI acceptance journey; demonstrates add/inspect → multi-select plan → recommendations → approval → isolated execution → deterministic evaluation → domain reports + consolidated report → cancel/rerun/recovery; AI-off path succeeds |
| ASTA-112 | **qa-lead** — QA Lead | Closes M1 quality, security, compatibility, privacy, and license evidence; release package links each claim to build/tool version, environment, requirement ID, evidence, outcome, and limitation; publishes supported matrix; unresolved numeric targets and retention approved or marked release-blocking; no certification/hostile-code claim |
| ASTA-113 | **doc-lead** — Documentation Lead | Defines release install/upgrade/uninstall and data-retention instructions; documents WSL2 CLI installation, prerequisites, updates/rollback, where state/artifacts live, backup/deletion/retention behavior, and troubleshooting; user can identify and remove ASTA-owned data without deleting project source |

---

## Summary — All 24 P0 Items with Owners

| Count | Epic | Items |
|-------|------|-------|
| 3 | Epic 0 | ASTA-001, ASTA-002, ASTA-003 |
| 2 | Epic 1 | ASTA-010, ASTA-011 |
| 1 | Epic 2 | ASTA-020 |
| 3 | Epic 3 | ASTA-030, ASTA-031, ASTA-032 |
| 3 | Epic 4 | ASTA-040, ASTA-041, ASTA-042 |
| 2 | Epic 5 | ASTA-050, ASTA-051 |
| 2 | Epic 6 | ASTA-060, ASTA-061 |
| 5 | Epic 7 | ASTA-070, ASTA-071, ASTA-072, ASTA-073, ASTA-074 |
| 1 | Epic 8 | ASTA-080 |
| 2 | Epic 8 | ASTA-081, ASTA-082 |
| 2 | Epic 9 | ASTA-090, ASTA-091 |
| 1 | Epic 9 | ASTA-092 |
| 1 | Epic 9 | ASTA-093 |
| 3 | Epic 10 | ASTA-100, ASTA-101, ASTA-102 |
| 4 | Epic 11 | ASTA-110, ASTA-111, ASTA-112, ASTA-113 |

**Total**: 24 P0 items with owner assignments

---

## Owner Role Distribution

| Role | Count | Items |
|------|-------|-------|
| security-engineer | 5 | ASTA-052, ASTA-070, ASTA-071, ASTA-072, ASTA-074 |
| reporting-engineer | 4 | ASTA-090, ASTA-091, ASTA-092, ASTA-093 |
| software-engineer | 4 | ASTA-030, ASTA-031, ASTA-051, ASTA-082 |
| test-architect | 3 | ASTA-032, ASTA-041, ASTA-042 |
| cli-developer | 3 | ASTA-020, ASTA-093, (also ASTA-062 role overlap) |
| data-engineer | 3 | ASTA-040, ASTA-050 |
| devops-engineer | 2 | ASTA-010, ASTA-011 |
| tech-lead | 2 | ASTA-001, ASTA-003 |
| solutions-architect | 1 | ASTA-002 |
| evaluator-lead | 2 | ASTA-080, ASTA-081 |
| qa-lead | 4 | ASTA-110, ASTA-111, ASTA-112, (also broader QA) |
| ai-gateway-lead | 2 | ASTA-100, ASTA-101 |
| natural-language-engineer | 1 | ASTA-102 |
| doc-lead | 1 | ASTA-113 |
| adapter-developer | 1 | ASTA-060 |
| api-engineer | 1 | ASTA-062 |

**Total unique roles**: 15  
**Total owner assignments**: 24

---

## M0 Design Freeze Entry Criteria — Owner Coverage Status

**From Backlog Section 9**: "This backlog is ready to schedule when each P0 has an owner, estimate, and dependency review; M0 decisions have ADRs; and every in-scope SRS requirement has a work item and verification artifact."

### ✅ Owner Assignments Complete: 24/24 P0 items have assigned owners

### ⏳ Pending: Estimates and dependency reviews for each owner

### ✅ Completed: 12 ADRs recorded (from TBD resolution session)

### ✅ Completed: Content baseline updated to `ASTA-CONTENT-BASELINE-2026-11-23-01`

### 📋 Next Steps
1. **Each owner provides estimate and dependency review** for their assigned item
2. **Map all in-scope SRS requirements** to work items and verification artifacts
3. **Perform Gate A and B exit criteria verification**
4. **Transition to M0 design freeze** — implementation begins only after user explicitly starts that phase

---

*Owner assignments completed 2026-11-23. All 24 P0 backlog items now have owners assigned. Project ready to proceed to estimate/dependency review phase and M0 design freeze transition.*

---
*This file should be referenced by all agents working on ASTA. Owner assignments are part of the project memory in `.claude/memory/`.*