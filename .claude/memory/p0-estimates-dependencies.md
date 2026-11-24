---
name: p0-estimates-dependencies
description: Estimates and dependencies for all 24 P0 backlog items
metadata:
  type: project
  status: in-review
---

# P0 Backlog Item Estimates and Dependencies — ASTA Project

**Date**: 2026-11-23  
**Prepared by**: Session (on behalf of each assigned owner)  
**For review by**: User  
**Status**: Estimates and dependencies provided — user to review and approve  
**Baseline**: `ASTA-CONTENT-BASELINE-2026-11-23-01`  
**Total P0 Items**: 24 items across 11 epics  

---

## Estimate Scale

| Scale | Description | Approx. Effort |
|-------|-------------|----------------|
| **S (Small)** | Straightforward implementation; primarily coding/configuration based on already-decided specs; no new research needed | 1-2 days |
| **M (Medium)** | Implementation requires some research/prototyping; integrates decided specs; may have moderate complexity | 3-5 days |
| **L (Large)** | Significant implementation; requires prototyping, design decisions, or bridging undefined areas; may span multiple phases | 5-10 days |
| **XL (X-Large)** | Major component; may define new patterns or require substantial infrastructure; likely spans multiple sprints/phases | 10+ days |

All estimates are **relative** and assume:
- All TBD items are resolved (completed 2026-11-23)
- All 12 ADRs are recorded
- Content baseline `ASTA-CONTENT-BASELINE-2026-11-23-01` is authoritative
- Work is in WSL2 + Ubuntu 22.04 + Docker Desktop 4.30.x environment
- Python 3.12.x with pinned dependencies (pytest 8.2.x, HTTPX 0.27.x, Schemathesis 5.6.x)

---

## Item-by-Item Estimates and Dependencies

### Epic 0 — M0 Scope, Decisions, and Requirement Traceability

| Item | Owner | Estimate | Dependencies | Description |
|------|-------|----------|--------------|-------------|
| ASTA-001 | tech-lead | **S** (1 day) | None (foundational) | Create M1 requirement-to-work-item ledger; map every in-scope SRS requirement to a backlog item; mark exclusions Later/Out of Scope; ensure no SRS ID silently dropped |
| ASTA-002 | solutions-architect | **S** (1 day) | ASTA-001 | Record approved M1 technical defaults and remaining implementation decisions as ADRs; distinguish confirmed decisions from proposed tools; exact API adapter versions, resource defaults, retention, schema fields, archive caps, and installation details with owners |
| ASTA-003 | tech-lead | **S** (1 day) | ASTA-001, ASTA-002 | Freeze M1 support matrix and trust claims; publish exact Windows/WSL2/Docker/ASTA-Python/pytest/API-adapter combinations only after verification; state trusted/authorized project execution limitation until isolation proof passes |

**Epic 0 Subtotal**: **S** (3 days)  
**Critical Path**: ASTA-001 → ASTA-002 → ASTA-003 (sequential, 3 days total)

---

### Epic 1 — Reproducible Windows + WSL2 + Docker Developer Environment

| Item | Owner | Estimate | Dependencies | Description |
|------|-------|----------|--------------|-------------|
| ASTA-010 | devops-engineer | **S** (2 days) | None | Define supported local development setup; give tested Windows and WSL2 prerequisites, Linux distribution recommendation, Docker Desktop WSL2 setup, repository location, Python 3.14 setup, and diagnostic commands; unsupported prerequisite produces actionable guidance |
| ASTA-011 | devops-engineer | **M** (3 days) | ASTA-010 | Define container image lifecycle and provenance; worker image versioned and reproducible; image update separate from target project; image/tool versions appear in run evidence; no implicit image pull/execution without configured policy |

**Epic 1 Subtotal**: **M** (5 days)  
**Dependencies**: ASTA-010 must complete before ASTA-011 (environment definition before image lifecycle)

---

### Epic 2 — CLI Contract and Input/Configuration

| Item | Owner | Estimate | Dependencies | Description |
|------|-------|----------|--------------|-------------|
| ASTA-020 | cli-developer | **M** (4 days) | None (but depends on ASTA-003 completion) | CLI contract supports intake/inspect, plan/review, approve, run, status, cancel, report, and supported rerun/recovery journey; help text documents flags and exit codes; commands cannot bypass policy; final command spellings reviewed before implementation |

**Epic 2 Subtotal**: **M** (4 days)  
**Dependencies**: ASTA-003 (support matrix freeze) should complete before, or concurrently with, ASTA-020 (command spellings depend on frozen matrix)

---

### Epic 3 — Project Intake, Inspection, and Capabilities

| Item | Owner | Estimate | Dependencies | Description |
|------|-------|----------|--------------|-------------|
| ASTA-030 | software-engineer | **M** (5 days) | ASTA-020 | Implement local-folder project intake and provenance; canonicalize path, record source/revision where available, reject unsupported/malformed input before execution, do not mutate source; project ownership/authorization confirmation captured |
| ASTA-031 | software-engineer | **L** (7 days) | ASTA-030, ASTA-032 | Implement safe static project inspection; detect Python manifests, pytest config/tests, OpenAPI descriptions, and supported signals without importing/executing project modules; every fact has evidence; unknown remains unknown |
| ASTA-032 | test-architect | **M** (5 days) | ASTA-030, ASTA-031, ASTA-040 | Register initial capability set and applicability states; only verified Python/pytest and API capabilities may be executable; states distinguish Applicable, Not applicable, Unsupported, Blocked, Awaiting authorization; reasons/prerequisites reported; project signals do not authorize execution |

**Epic 3 Subtotal**: **L** (14 days, but parallelizable)  
**Dependencies**: 
- ASTA-030 must complete before ASTA-031 and ASTA-032 (intake before capability registration and inspection)
- ASTA-031 and ASTA-032 can proceed in parallel after ASTA-030 completion
- ASTA-032 depends on ASTA-040 (taxonomy model) for capability-taxonomy alignment

---

### Epic 4 — Taxonomy, Planner, Recommendations, and Approvals

| Item | Owner | Estimate | Dependencies | Description |
|------|-------|----------|--------------|-------------|
| ASTA-040 | data-engineer | **M** (4 days) | ASTA-032, ASTA-041 | Implement versioned normalized taxonomy model; preserve separate dimensions: test level/strategy, domain, protocol/platform, technique, validation intent; one check can carry multiple tags; stable IDs/alias policy versioned before persisted runs |
| ASTA-041 | test-architect | **M** (5 days) | ASTA-032, ASTA-040 | Implement deterministic planner within user-approved scope; planner uses evidence and adapter manifests; classifies applicability; does not create out-of-scope execution; distinguishes included, excluded, blocked, unsupported, not applicable, pending recommendation |
| ASTA-042 | test-architect | **L** (7 days) | ASTA-041, ASTA-043, ASTA-032 | Implement recommendation review and exact approval binding; each recommendation includes rationale/evidence/risk/prerequisites; approved additions bind to run, exact scope, plan revision/content hash and policy version; declined/pending never execute; material change invalidates approval and is audited |

**Epic 4 Subtotal**: **L** (13 days, parallelizable with coordination)  
**Dependencies**: 
- ASTA-040 and ASTA-041 can proceed in parallel after ASTA-032 completion
- ASTA-042 depends on both ASTA-041 and ASTA-043 (language-boundary decision)
- All three benefit from early ASTA-020 (CLI contract) for plan output format

---

### Epic 5 — Persisted Workflow, Storage, and Audit

| Item | Owner | Estimate | Dependencies | Description |
|------|-------|----------|--------------|-------------|
| ASTA-050 | data-engineer | **M** (4 days) | None (but benefits from ASTA-011) | Approve physical data contracts and local persistence design; decide IDs, immutable snapshots, DB schema/migrations, report schema_version, artifact digest, file/DB consistency, locking, backup/deletion/retention; record ADRs before persistence implementation |
| ASTA-051 | software-engineer | **L** (6 days) | ASTA-050, ASTA-052 | Implement persisted state machine with one active worker; state transitions guarded and persisted; restart resumes/marks run deterministically; concurrent start cannot create conflicting active worker; idempotent cancel/rerun behavior; immutable run snapshot preserved |
| ASTA-052 | security-engineer | **M** (4 days) | ASTA-050, ASTA-070 | Implement audit events for security and lifecycle decisions; audit target decisions, approvals, plan revisions, egress decisions, credential references, cancellation, AI provider/data-sharing event, artifact access; no secret values; each decision has actor/source, time, policy version, and reason |

**Epic 5 Subtotal**: **L** (11 days, partial parallelization)  
**Dependencies**: 
- ASTA-050 must complete before ASTA-051 (data contracts before state machine)
- ASTA-051 and ASTA-052 can proceed in parallel after ASTA-050 completion
- All benefit from ASTA-070 (isolated worker) for audit event validation context

---

### Epic 6 — Adapter Contract and Initial Python/pytest Adapter

| Item | Owner | Estimate | Dependencies | Description |
|------|-------|----------|--------------|-------------|
| ASTA-060 | adapter-developer | **M** (4 days) | ASTA-050, ASTA-040 | Approve adapter manifest and output schemas; manifest includes stable adapter_id, capabilities/tags, applicability evidence, support state, risk, prerequisites, tool/version/license, OS/runtime, allowlisted command/input, output schema, evidence mapping, limits, unsupported conditions |
| ASTA-061 | software-engineer | **L** (7 days) | ASTA-060, ASTA-051, ASTA-080 | Implement existing pytest execution adapter; runs only explicit approved test command in isolated worker; captures exit/stdout/stderr/timing/tool version and raw evidence; does not modify source; missing runtime/prerequisite is Blocked or Unsupported; adapter does not assign overall verdict |
| ASTA-062 | api-engineer | **L** (7 days) | ASTA-060, ASTA-051, ASTA-070, ASTA-071 | Implement OpenAPI API-check adapter; supports only approved OpenAPI version(s) and exact authorized target; reject spec URLs/redirects that expand scope; HTTPX transport and Schemathesis use only if version/license/parser verified; request rate, timeout, redaction, and output caps enforced; preserve request/response/schema provenance |

**Epic 6 Subtotal**: **L** (13 days, parallel with coordination)  
**Dependencies**: 
- ASTA-060 must complete before ASTA-061 and ASTA-062 (manifest approval before adapter implementation)
- ASTA-061 depends on ASTA-051 (state machine) and ASTA-080 (evaluator)
- ASTA-062 depends on ASTA-051 (state machine), ASTA-070 (worker), ASTA-071 (egress)
- All three depend on ASTA-040 (taxonomy) for adapter capability classification

---

### Epic 7 — Isolation, Egress, Resources, and Safety Release Gate

| Item | Owner | Estimate | Dependencies | Description |
|------|-------|----------|--------------|-------------|
| ASTA-070 | security-engineer | **L** (6 days) | ASTA-010, ASTA-012, ASTA-051 | Implement disposable isolated execution worker; worker has no Docker socket, privileged mode, host networking, host home, or host-wide environment; source is read-only; output is separate; non-root where supported; capabilities reduced; container/process cleanup on every exit |
| ASTA-071 | security-engineer | **M** (4 days) | ASTA-070, ASTA-060 | Implement deny-by-default egress enforcement; worker has no network unless approved check needs it; all requests/redirects and DNS-resolved addresses rechecked; exact target only; deny localhost/private/link-local/metadata unless explicitly approved; separate approved registry access for dependency-install phase |
| ASTA-072 | performance-engineer | **M** (4 days) | ASTA-070 | Enforce resource and output limits; CPU, memory, process count, disk, output size, wall-clock, and API rate limits enforced; numerical defaults approved from representative workload measurements; limit cause captured as evidence and canonical outcome |
| ASTA-073 | software-engineer | **M** (5 days) | ASTA-051, ASTA-070 | Verify worker cancellation, timeout, crash recovery, and cleanup; cancel/timeout/crash stops process group and removes worker/network/temp volumes/credential access; preserves completed attempts and partial evidence; records cleanup success/failure; never reports a false pass |
| ASTA-074 | security-engineer | **XL** (10 days) | ASTA-070, ASTA-071, ASTA-072, ASTA-010 | Pass adversarial isolation and target-boundary acceptance suite; demonstrate host-file/socket denial, no source writes, resource caps, DNS rebinding, direct IPv4/IPv6, redirect, local/private/link-local/metadata denial, target allow case, archive/path attacks if applicable, oversized output, cancellation, cleanup, and secret-canary redaction; if any critical case fails, disable project-code execution and release only read-only analysis/trusted-project mode |

**Epic 7 Subtotal**: **XL** (21 days, but parallelizable with strong coordination)  
**Dependencies**: 
- ASTA-010 (WSL/Docker env) is foundational for all 5 items
- ASTA-070 (isolated worker) is dependency for ASTA-071, ASTA-072, ASTA-073, ASTA-074
- ASTA-071 depends on ASTA-070 and ASTA-060 (manifest)
- ASTA-072 depends on ASTA-070
- ASTA-073 depends on ASTA-051 (state machine) and ASTA-070
- ASTA-074 depends on ASTA-070, ASTA-071, ASTA-072 (all safety gates)
- This is the **critical path** for M1 safety validation

---

### Epic 8 — Deterministic Evaluator and Traceability/Change-Aware Behavior

| Item | Owner | Estimate | Dependencies | Description |
|------|-------|----------|--------------|-------------|
| ASTA-080 | evaluator-lead | **M** (4 days) | ASTA-050, ASTA-063 | Implement deterministic expectation and result evaluator; consumes stored evidence/expectation/policy only; no AI dependency/import; only user criteria, formal specification, existing test, configured threshold, or defined universal check can authoritatively pass/fail; AI-only expectation is Inconclusive |
| ASTA-081 | evaluator-lead | **M** (4 days) | ASTA-080, ASTA-061 | Implement exact retry/flaky/timeout/overall verdict rules; fail then pass retry becomes Flaky; preserve all attempts; timeout is Failed only for explicit configured timeout assertion, otherwise Error; overall verdict exactly follows contract; no pass if required evidence persistence/reporting fails |
| ASTA-082 | software-engineer | **M** (4 days) | ASTA-080, ASTA-030, ASTA-031 | Implement source revision and change-impact traceability; store source revision/hash and links among requirements, checks, attempts, findings, evidence, and reports; unchanged scope may reuse evidence only when compatibility/freshness is proven; changed target/plan invalidates approval; unsupported change analysis is clearly not measured |

**Epic 8 Subtotal**: **M** (10 days, parallelizable)  
**Dependencies**: 
- ASTA-080 and ASTA-081 are sequential (evaluator then verdict rules)
- ASTA-082 depends on ASTA-080 (evaluator) and ASTA-030/ASTA-031 (project intake/inspection for source-change mapping)

---

### Epic 9 — Reporting, Artifacts, and User Review

| Item | Owner | Estimate | Dependencies | Description |
|------|-------|----------|--------------|-------------|
| ASTA-090 | reporting-engineer | **M** (4 days) | ASTA-050, ASTA-080 | Approve report JSON schema and artifact contract; define exact schema_version, field names, timestamps, enums, nullability, redaction metadata, artifact digest, compatibility evolution; validate before report implementation |
| ASTA-091 | reporting-engineer | **M** (4 days) | ASTA-090, ASTA-080, ASTA-082 | Compose one report for each selected domain and one consolidated report; multi-domain run emits every selected domain report plus one consolidated report; counts/verdicts reconcile; include target/scope, environment, timing, plan, expectations/provenance, adapter/tool versions, all dispositions, evidence, limitations, recommendations, and tested-scope qualification |
| ASTA-092 | reporting-engineer | **M** (4 days) | ASTA-090, ASTA-091 | Write Markdown and versioned JSON reports safely; Markdown is readable; JSON validates against approved schema; artifact IDs resolve safely; hashes/provenance checked; secrets redacted; malicious text/HTML and traversal safely handled; missing/corrupt artifact is explicit |
| ASTA-093 | cli-developer | **M** (3 days) | ASTA-091, ASTA-020 | Add conditional JUnit XML output for pytest-compatible CI use; emit only if status/finding mapping validated; retain canonical JSON/Markdown as authoritative; document unsupported mapping; CLI exit code matches documented run verdict policy |

**Epic 9 Subtotal**: **M** (13 days, parallelizable)  
**Dependencies**: 
- ASTA-090 must complete before ASTA-091 and ASTA-092 (schema approval before report composition and writing)
- ASTA-091 and ASTA-092 can proceed in parallel after ASTA-090 completion
- ASTA-093 depends on ASTA-091 (report composition) and ASTA-020 (CLI contract for command spellings/exit codes)

---

### Epic 10 — AI Gateway and Natural-Language Assistance

| Item | Owner | Estimate | Dependencies | Description |
|------|-------|----------|--------------|-------------|
| ASTA-100 | ai-gateway-lead | **S** (2 days) | ASTA-020 | Ensure complete AI-off workflow; intake, inspect, plan, approve, run, evaluate, report, cancel/recover do not require a model; missing/unconfigured model cannot block deterministic supported workflow |
| ASTA-101 | ai-gateway-lead | **M** (4 days) | ASTA-100, ASTA-052 | Add bounded local-model gateway only after provider is configured; local provider off by default; explicit config required; bounded inputs/output, schema validation, timeout/retry caps, provenance and opt-in audit; model cannot execute commands, alter scope, approve, change policy, or set verdict; invalid/unavailable provider degrades safely |
| ASTA-102 | natural-language-engineer | **M** (4 days) | ASTA-100, ASTA-022, ASTA-041 | Implement natural-language selection normalization and conversion; request converted into proposed canonical selections; user reviews final plan; ambiguous intent asks clarification; unavailable AI uses deterministic parsing or reports unsupported; AI suggestions remain recommendations until exact approval |

**Epic 10 Subtotal**: **M** (8 days, parallelizable)  
**Dependencies**: 
- ASTA-100 is foundational for ASTA-101
- ASTA-102 depends on ASTA-100 (AI-off workflow) and ASTA-022 (scope input normalization) and ASTA-041 (planner for classification)
- All three benefit from ASTA-020 (CLI contract) for command/output consistency

---

### Epic 11 — Release Acceptance, Evidence, and Support Claims

| Item | Owner | Estimate | Dependencies | Description |
|------|-------|----------|--------------|-------------|
| ASTA-110 | qa-lead | **M** (4 days) | ASTA-061, ASTA-062, ASTA-080 | Build representative Python/API bug-garden fixtures; controlled fixtures include known passing/failing tests, API contract cases, missing oracle, unsupported combination, and flaky/retry behavior; benchmark answer keys not exposed to planner/worker; no numeric recall threshold claimed until approved |
| ASTA-111 | qa-lead | **L** (6 days) | ASTA-110, ASTA-020–ASTA-102 | Run full M1 CLI acceptance journey; demonstrate add/inspect → multi-select plan → recommendations → approval → isolated execution → deterministic evaluation → domain reports + consolidated report → cancel/rerun/recovery; AI-off path succeeds |
| ASTA-112 | qa-lead | **L** (6 days) | ASTA-111, ASTA-074, ASTA-091–ASTA-111 | Close M1 quality, security, compatibility, privacy, and license evidence; release package links each claim to build/tool version, environment, requirement ID, evidence, outcome, and limitation; publish supported matrix; unresolved numeric targets and retention approved or marked release-blocking; no certification/hostile-code claim |
| ASTA-113 | doc-lead | **M** (3 days) | ASTA-112, ASTA-010, ASTA-050 | Define release install/upgrade/uninstall and data-retention instructions; document WSL2 CLI installation, prerequisites, updates/rollback, where state/artifacts live, backup/deletion/retention behavior, and troubleshooting; user can identify and remove ASTA-owned data without deleting project source |

**Epic 11 Subtotal**: **L** (15 days, parallelizable with coordination)  
**Dependencies**: 
- ASTA-110 depends on ASTA-061 (pytest adapter) and ASTA-062 (API adapter) and ASTA-080 (evaluator)
- ASTA-111 depends on ASTA-110 (all-fixtures) and ALL CLI/plan/execution items (ASTA-020 through ASTA-102)
- ASTA-112 depends on ASTA-111 (full journey) and ASTA-074 (adversarial isolation proof) and ASTA-091–ASTA-111 (reporting evidence)
- ASTA-113 depends on ASTA-112 (evidence package) and ASTA-010 (WSL2 install guide) and ASTA-050 (artifact retention docs)

---

## Summary — All 24 P0 Items with Estimates and Dependencies

| Epic | Item | Estimate | Key Dependencies |
|------|------|----------|-----------------|
| 0 | ASTA-001 | S (1d) | None |
| 0 | ASTA-002 | S (1d) | ASTA-001 |
| 0 | ASTA-003 | S (1d) | ASTA-001, ASTA-002 |
| 1 | ASTA-010 | S (2d) | None |
| 1 | ASTA-011 | M (3d) | ASTA-010 |
| 2 | ASTA-020 | M (4d) | ASTA-003 (ideally) |
| 3 | ASTA-030 | M (5d) | ASTA-020 |
| 3 | ASTA-031 | L (7d) | ASTA-030, ASTA-032 |
| 3 | ASTA-032 | M (5d) | ASTA-030, ASTA-031, ASTA-040 |
| 4 | ASTA-040 | M (4d) | ASTA-032, ASTA-041 |
| 4 | ASTA-041 | M (5d) | ASTA-032, ASTA-040 |
| 4 | ASTA-042 | L (7d) | ASTA-041, ASTA-043, ASTA-032 |
| 5 | ASTA-050 | M (4d) | None (benefits from ASTA-011) |
| 5 | ASTA-051 | L (6d) | ASTA-050, ASTA-052 |
| 5 | ASTA-052 | M (4d) | ASTA-050, ASTA-070 |
| 6 | ASTA-060 | M (4d) | ASTA-050, ASTA-040 |
| 6 | ASTA-061 | L (7d) | ASTA-060, ASTA-051, ASTA-080 |
| 6 | ASTA-062 | L (7d) | ASTA-060, ASTA-051, ASTA-070, ASTA-071 |
| 7 | ASTA-070 | L (6d) | ASTA-010, ASTA-012, ASTA-051 |
| 7 | ASTA-071 | M (4d) | ASTA-070, ASTA-060 |
| 7 | ASTA-072 | M (4d) | ASTA-070 |
| 7 | ASTA-073 | M (5d) | ASTA-051, ASTA-070 |
| 7 | ASTA-074 | XL (10d) | ASTA-070, ASTA-071, ASTA-072, ASTA-010 |
| 8 | ASTA-080 | M (4d) | ASTA-050, ASTA-063 |
| 8 | ASTA-081 | M (4d) | ASTA-080, ASTA-061 |
| 8 | ASTA-082 | M (4d) | ASTA-080, ASTA-030, ASTA-031 |
| 9 | ASTA-090 | M (4d) | ASTA-050, ASTA-080 |
| 9 | ASTA-091 | M (4d) | ASTA-090, ASTA-080, ASTA-082 |
| 9 | ASTA-092 | M (4d) | ASTA-090, ASTA-091 |
| 9 | ASTA-093 | M (3d) | ASTA-091, ASTA-020 |
| 10 | ASTA-100 | S (2d) | ASTA-020 |
| 10 | ASTA-101 | M (4d) | ASTA-100, ASTA-052 |
| 10 | ASTA-102 | M (4d) | ASTA-100, ASTA-022, ASTA-041 |
| 11 | ASTA-110 | M (4d) | ASTA-061, ASTA-062, ASTA-080 |
| 11 | ASTA-111 | L (6d) | ASTA-110, ASTA-020–ASTA-102 |
| 11 | ASTA-112 | L (6d) | ASTA-111, ASTA-074, ASTA-091–ASTA-111 |
| 11 | ASTA-113 | M (3d) | ASTA-112, ASTA-010, ASTA-050 |

### 📊 Estimated Totals by Scale

| Scale | Item Count | Total Approx. Effort |
|-------|------------|---------------------|
| **S (Small)** | 5 items | ~5 days |
| **M (Medium)** | 12 items | ~44 days |
| **L (Large)** | 7 items | ~41 days |
| **XL (X-Large)** | 1 item (ASTA-074) | ~10 days |

**Grand Total Estimated Effort**: **~140 days** (approximately 28 work days per month, or ~5-6 person-months for a single developer, or ~2-3 people for 2-3 months)

### 🔗 Critical Path Analysis

**Longest dependency chain** (critical path for M0 completion):

1. ASTA-010 (2d) → ASTA-011 (3d) → ASTA-050 (4d) → ASTA-051 (6d) → ASTA-070 (6d) → ASTA-074 (10d)
   - **Subtotal**: 32 days (but many items can parallelize)

**Alternative critical path**:

1. ASTA-010 (2d) → ASTA-030 (5d) → ASTA-031 (7d) → ASTA-042 (7d) → ASTA-041 (5d) — but these parallelize with other tracks

**Realistic M0 completion** (with proper parallelization across 15 roles):
- **Best case**: 20-25 days if all owners start immediately and parallelize effectively
- **Typical case**: 30-35 days with normal coordination and some sequential dependencies
- **Conservative case**: 40-45 days if dependencies reveal unexpected complexities

### 📋 Dependency Highlights (Must-Resolve Before Proceeding)

**Hard dependencies** (item cannot start until dependency completes):
1. **ASTA-010 → ASTA-011**: Environment definition before image lifecycle
2. **ASTA-030 → ASTA-031, ASTA-032**: Intake before capability registration/inspection
3. **ASTA-030 → ASTA-040, ASTA-041, ASTA-042**: Intake before taxonomy/planner/recommendations
4. **ASTA-050 → ASTA-051**: Data contracts before state machine
5. **ASTA-060 → ASTA-061, ASTA-062**: Manifest approval before adapter implementation
6. **ASTA-070 → ASTA-071, ASTA-072, ASTA-073, ASTA-074**: Isolated worker before all safety gates
7. **ASTA-080 → ASTA-081**: Evaluator before verdict rules
8. **ASTA-090 → ASTA-091, ASTA-092**: Schema approval before report composition/writing
9. **ASTA-110 → ASTA-111**: Fixtures before full acceptance journey

**Soft dependencies** (recommended timing, not strict blocks):
- ASTA-020 should align with ASTA-003 (CLI commands depend on frozen support matrix)
- ASTA-040, ASTA-041, ASTA-042 benefit from early ASTA-020 (CLI output format)
- ASTA-051, ASTA-052, ASTA-071, ASTA-073 benefit from ASTA-070 (worker implementation)
- ASTA-111 depends on nearly all prior items (full journey)

---

## 👥 Owner Assignment + Estimate + Dependency Summary

| Owner | # Items | Total Estimate | Key Items |
|-------|---------|----------------|-----------|
| security-engineer | 5 | ~23 days | ASTA-052, ASTA-070, ASTA-071, ASTA-072, ASTA-074 |
| reporting-engineer | 4 | ~13 days | ASTA-090, ASTA-091, ASTA-092, ASTA-093 |
| software-engineer | 4 | ~23 days | ASTA-030, ASTA-031, ASTA-051, ASTA-082 |
| test-architect | 3 | ~14 days | ASTA-032, ASTA-041, ASTA-042 |
| cli-developer | 3 | ~7 days | ASTA-020, ASTA-093 |
| data-engineer | 3 | ~10 days | ASTA-040, ASTA-050 |
| devops-engineer | 2 | ~5 days | ASTA-010, ASTA-011 |
| tech-lead | 2 | ~2 days | ASTA-001, ASTA-003 |
| solutions-architect | 1 | ~1 day | ASTA-002 |
| evaluator-lead | 2 | ~8 days | ASTA-080, ASTA-081 |
| qa-lead | 4 | ~16 days | ASTA-110, ASTA-111, ASTA-112 |
| ai-gateway-lead | 2 | ~6 days | ASTA-100, ASTA-101 |
| natural-language-engineer | 1 | ~4 days | ASTA-102 |
| adapter-developer | 1 | ~4 days | ASTA-060 |
| api-engineer | 1 | ~7 days | ASTA-062 |
| doc-lead | 1 | ~3 days | ASTA-113 |

**Total**: 24 items, ~140 days aggregate, ~15 unique roles

---

## ✅ User Review Request

**Please review the following and provide feedback:**

1. **Estimate reasonableness**: Do the S/M/L/XL scales seem appropriate for your context? Would you prefer person-days, story points, or another estimation unit?

2. **Dependency accuracy**: Are the dependency chains correct based on your understanding of the project? Are there missing dependencies or incorrect dependencies?

3. **Owner feasibility**: Do the assigned owners have reasonable workloads (24 items across 15 roles, ~1.6 items per role average)? Should any items be reassigned?

4. **Critical path**: Is the identified critical path (especially ASTA-074 adversarial suite) correct for your M0/M1 goals?

5. **Estimation scope**: Should estimates be "effort to complete" or "complexity/risk level"? Should they include verification/testing time?

6. **M0 exit criteria**: Do these estimates and dependencies support the M0 design freeze entry criteria (each P0 has owner, estimate, dependency review)?

**Next steps after your review**:
- Adjust estimates/dependencies as needed
- Owners formally accept their estimates and identify any blocking dependencies
- Proceed to M0 design freeze transition
- Begin M1a (Safe skeleton) implementation

---

*Estimates and dependencies provided 2026-11-23 on behalf of all 24 P0 item owners. User to review and approve before proceeding to M0 design freeze transition.*

---
*This file should be referenced by all agents working on ASTA. Estimates and dependencies are part of the project memory in `.claude/memory/`.*