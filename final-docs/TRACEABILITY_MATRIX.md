# ASTA Requirements Traceability Matrix

**Status:** Baseline mapping  
**Normative source:** [`SRS.md`](SRS.md)  
**Related:** [`PRD.md`](PRD.md), [`TAD.md`](TAD.md), [`VERIFICATION_AND_QUALITY_PLAN.md`](VERIFICATION_AND_QUALITY_PLAN.md)

## 1. Purpose and rules

This matrix connects the product goals and every requirement family in the SRS to design responsibilities and verification evidence. The SRS remains authoritative for the complete requirement wording, priority, phase, and per-requirement verification statement. This file is an index and does not replace those details.

- Do not mark a requirement complete because a component exists; completion requires its specified evidence.
- A missing adapter, unsupported environment, or unmet prerequisite is a visible result, never a silently omitted requirement.
- If a requirement lacks an observable acceptance condition, clarify the SRS before implementation.
- `TBD` performance, retention, platform, and benchmark values remain release blockers where the SRS says they must be approved before release.

## 2. Product goal trace

| Product outcome | PRD/TAD location | SRS requirement references | Design responsibility | Verification evidence |
|---|---|---|---|---|
| Let users select appropriate test scope and see applicability/reasons | PRD §§5–8; TAD §§5–6 | `IF-CLI-002`, `IF-CLI-003`, `IF-CFG-001`; `FR-INS-001`–`FR-INS-006`; `FR-SCOPE-003`–`FR-SCOPE-008`; `FR-PLAN-001`–`FR-PLAN-006` | Inspector, capability registry, taxonomy resolver, planner, approval service | Known project fixtures; multi-select resolution; all applicability states; out-of-scope and changed-plan approvals blocked |
| Produce reproducible checks and evidence-backed results | PRD §§7, 10; TAD §§7, 10 | `FR-GEN-001`–`FR-GEN-007`; `FR-EXEC-001`–`FR-EXEC-009`; `FR-EVAL-001`–`FR-EVAL-010`; `FR-REP-001`–`FR-REP-008`; `NFR-REL-001`–`NFR-REL-003` | Generator, adapters, worker, evaluator, artifact store, report composer | Replay fixture with no model call; evaluator golden cases; artifact reference validation; source hash unchanged |
| Keep execution authorized and bounded | PRD §§5, 9–10; TAD §8 | `IF-CLI-004`, `IF-CFG-003`; `FR-SCOPE-001`, `FR-SCOPE-002`, `FR-SCOPE-005`–`FR-SCOPE-007`; `FR-EXEC-001`–`FR-EXEC-010`; `NFR-SEC-001`–`NFR-SEC-006`; `NFR-PRIV-001`–`NFR-PRIV-002` | Intake/authorization gate, risk gate, egress controller, secrets manager, sandbox, worker, audit | Scope bypass and network tests; canary secret tests; archive adversarial fixtures; missing-approval/no-sandbox runs start no worker |
| Keep AI advisory, bounded, and optional | PRD §§1, 5, 7; TAD §9 | `FR-AI-001`–`FR-AI-007`; `NFR-SEC-005`; `NFR-MAINT-002` | AI gateway and bounded planning/generation assistance; deterministic evaluator remains isolated | AI-off end-to-end run; malformed-output fallback; prompt-injection fixtures; no AI import/call from evaluator, reporter, or sandbox |
| Give users trustworthy per-domain and consolidated reporting | PRD §§1, 7, 10; TAD §§10–11 | `FR-REP-001`–`FR-REP-009`; `FR-EVAL-007`–`FR-EVAL-010` | Deterministic evaluator, evidence store, domain report composer, consolidated report composer | Multi-domain output contains each individual report plus consolidated output; every status/gap/evidence reference reconciles |
| Support growth without changing the engine per interface | PRD §§7–8; TAD §§3, 7, 12 | `IF-CLI-001`–`IF-CLI-004`; `IF-MCP-001`; `IF-API-001`–`IF-API-002`; `IF-UI-001`; `FR-INS-004`–`FR-INS-005`; `NFR-MAINT-001`; `NFR-SCALE-002` | Shared application services; thin CLI/MCP/API/UI adapters; versioned adapter registry | Equivalent request produces equivalent plan/evaluation; fake adapter can be added without core change; interface contract checks |

## 3. SRS requirement inventory by verification owner

The following lists enumerate the exact requirement IDs in the current SRS. Detailed wording and phase remain in the SRS.

| Verification owner / area | Requirement IDs | Minimum evidence class |
|---|---|---|
| CLI | `IF-CLI-001`–`IF-CLI-004` | Demonstration + automated end-to-end; command and exit-code contract |
| Configuration | `IF-CFG-001`–`IF-CFG-003` | Schema validation, invalid-config/no-side-effect checks, policy-conflict fixture |
| MCP | `IF-MCP-001` | Contract equivalence and approval-boundary checks |
| REST API | `IF-API-001`–`IF-API-002` | Schema/auth/error contract tests before M3 declaration |
| Web UI | `IF-UI-001` | Browser acceptance, keyboard/semantic review |
| Intake/lifecycle | `FR-PROJ-001`–`FR-PROJ-005` | Source fixtures, archive attacks, provenance and deletion audit |
| Scope/authorization/risk | `FR-SCOPE-001`–`FR-SCOPE-008` | Scope/redirect/IP/approval/secret canaries and state fixtures |
| Inspection/capability | `FR-INS-001`–`FR-INS-007` | Known/unknown project fixtures, no-import hostile initialization, change mapping if enabled |
| Planning/approval | `FR-PLAN-001`–`FR-PLAN-006` | Plan revision, recommendation, edit, exclusion, and approval invalidation fixtures |
| Generation/language boundary | `FR-GEN-001`–`FR-GEN-007` | Existing test/schema preference, script validation, source hash, language binding fixtures |
| Execution/job control | `FR-EXEC-001`–`FR-EXEC-010` | Resource-exhaustion, network, cancellation, crash/restart, cleanup and risk fixtures |
| Evaluation | `FR-EVAL-001`–`FR-EVAL-010` | Deterministic golden suite for each status, oracle, retry, timeout, verdict, and “not measured” |
| AI / analysis | `FR-AI-001`–`FR-AI-007`; `FR-AN-001`–`FR-AN-002` | Schema/refusal/retry/offline/injection/provider audit and comparison fixtures |
| Reports/artifacts | `FR-REP-001`–`FR-REP-009` | Schema validation, report completeness, redaction, per-domain + consolidated output |
| Configuration/fix mode | `FR-CONF-001`–`FR-CONF-005` | Immutable run snapshot; provider audit; fix mode disabled/approval/original-source preservation |
| Security/privacy | `NFR-SEC-001`–`NFR-SEC-006`; `NFR-PRIV-001`–`NFR-PRIV-002` | Threat-model controls and adversarial proof; retention/deletion and remote-content audit |
| Reliability/performance/scaling | `NFR-REL-001`–`NFR-REL-003`; `NFR-PERF-001`–`NFR-PERF-004`; `NFR-SCALE-001`–`NFR-SCALE-002` | Restart/replay/cancel tests, resource measurements, approved numeric target evidence |
| Usability/maintenance/operations | `NFR-USE-001`–`NFR-USE-002`; `NFR-MAINT-001`–`NFR-MAINT-002`; `NFR-OBS-001` | UI and CLI walkthrough, adapter manifest checks, dependency boundary and log-redaction checks |
| Compatibility/licensing | `NFR-COMP-001`–`NFR-COMP-002`; `NFR-LIC-001` | Published support matrix, legal/licensing review, claim wording review |

Use cases `UC-01` through `UC-06` are end-to-end scenarios in SRS §10 and must be included in the release evidence set: create/inspect, plan/approve, execute, review, cancel/rerun, and AI-provider-unavailable behavior.

## 4. Requirement change and closure record

For implementation tracking, append one row per SRS requirement without changing its ID:

| Requirement ID | Baseline version | Design component | Verification case/artifact | Result | Evidence location | Owner | Status |
|---|---|---|---|---|---|---|---|
| Example: `FR-SCOPE-002` | SRS version TBD | Risk/target gate + egress controller | Direct IP, redirect, IPv6, DNS, changed-manifest cases | TBD | TBD | TBD | Not started |

Permitted closure states: `Not started`, `In progress`, `Blocked`, `Pass`, `Fail`, `Waived by approved change`. A waiver must identify the approving stakeholder, rationale, replacement control (if any), and affected release. No waivers are currently recorded.

