# ASTA M1 CLI Implementation Backlog

**Document status:** Planning baseline, ready for implementation planning review  
**Release target:** M1 — local CLI for Windows developers using WSL2 and Docker  
**Implementation status:** Not started; this backlog does not claim that code, tests, or security controls exist.  
**Baseline source:** `final-docs/PRD.md`, `SRS.md`, `TAD.md`, `ADR_REGISTER.md`, `INTERFACE_AND_WORKFLOW_SPEC.md`, `TAXONOMY_AND_ADAPTER_MATRIX.md`, `DATA_AND_ARTIFACT_CONTRACTS.md`, `SECURITY_THREAT_MODEL.md`, `FAILURE_RECOVERY_AND_STATE_MODEL.md`, `VERIFICATION_AND_QUALITY_PLAN.md`, and `TRACEABILITY_MATRIX.md`.

## 1. Purpose and planning rules

This backlog converts the current ASTA product and architecture baseline into an M1 implementation sequence. It does not replace the SRS requirement wording or IDs. Work items must link to the applicable SRS IDs in the traceability matrix, and completion requires recorded acceptance evidence.

Priority meanings:

- **P0 — Release blocker:** Required for M1; release cannot ship without passing its acceptance criteria.
- **P1 — M1 required:** Required for the agreed M1 user journey and product promise.
- **P2 — M1 conditional:** Include only if required by verified adapter support or a release decision; otherwise defer without implying support.
- **Later:** Explicitly outside M1, retained here to prevent accidental scope expansion.

Dependencies are named by backlog item ID. Acceptance criteria define observable behavior, not a claim that work is already complete. “No worker starts” means no test process or project-controlled code is launched by ASTA.

## 2. Approved M1 defaults

These defaults were approved as a set in project discussion and are treated as the M1 planning baseline:

1. **Product interface:** M1 is a local CLI. The user-facing installation is initially a CLI installed and run inside WSL2; a native Windows `.exe` is not an M1 requirement.
2. **Developer environment:** Windows 11, WSL2, and Docker Desktop using the WSL2 backend. Keep the working repository in the WSL Linux filesystem. Minimum setup checks must verify the current Docker/WSL prerequisites; Docker currently documents WSL 2.1.5+ for the backend and 2.6+ if Enhanced Container Isolation is required. ECI is Business-only and must not silently become a user prerequisite. See [Docker WSL2 backend requirements](https://docs.docker.com/desktop/features/wsl), [Docker Desktop for Windows requirements](https://docs.docker.com/desktop/setup/install/windows-install/), and [Enhanced Container Isolation](https://docs.docker.com/desktop/enterprise/hardened-desktop/enhanced-container-isolation/).
3. **Core runtime:** Python 3.14.x for ASTA itself. Publish only runtime and adapter combinations actually verified.
4. **Initial test support:** Existing Python/pytest suites plus scoped API checks described by an OpenAPI document. HTTPX is the proposed HTTP client and Schemathesis is a candidate for schema-derived cases; each dependency/tool still requires version, license, OS, and output-parser verification before being enabled.
5. **Test selection:** Multi-select across the normalized taxonomy. M1 execution support is limited to verified adapters; unsupported selections remain visible with reasons.
6. **Recommendations:** The agent may recommend additional tests, but the user must approve the exact added checks before execution. Approval binds to the run, scope, plan revision/content hash, and policy version; material changes invalidate affected approval.
7. **Reports:** Markdown and versioned JSON; individual report for every selected domain plus one consolidated report. JUnit XML is conditional on verified mapping; HTML is not required for M1.
8. **AI:** AI-off execution is the dependable default. Local model support is off until configured. AI cannot grant authorization, change scope/approval/policy, or assign verdicts. Exact model/provider is deferred.
9. **Configuration:** Versioned TOML project configuration; CLI flags override project configuration, which overrides built-in defaults. Invalid configuration fails before side effects. File name to use for the first schema: `asta.toml` (implementation naming choice).
10. **Network and credentials:** Network deny by default. Only explicitly approved targets are reachable for a check. Secrets are supplied per run through scoped environment injection or interactive input; do not persist plaintext values or pass the host-wide environment to workers. OS credential-store integration is deferred.
11. **Trust boundary:** M1 execution is limited to projects the operator is authorized to run while the isolation boundary is being validated. If the required boundary or egress enforcement is absent or unproven, allow only configured read-only analysis or block execution. Docker alone is not a hostile-code safety guarantee.
12. **Workflow/persistence:** Local persisted workflow, initially one active worker per machine. SQLite and local artifact files remain the planned implementation baseline subject to physical schema/migration decisions and crash-recovery proof.
13. **Results:** Preserve exact attempt states: `Passed`, `Failed`, `Flaky`, `Skipped`, `Blocked`, `Inconclusive`, `Unsupported`, `Error`. Overall verdicts remain `Failures found`, `Unreliable results`, `Passed in tested scope`, or `No result` under the evaluator contract.

## 3. M1 scope boundary

### Included in the first release

- Local project intake and source/profile inspection without executing project modules during static analysis.
- User selection through CLI flags/prompts, `asta.toml`, and natural-language requests; normalize requests to the versioned taxonomy and require clarification when ambiguous.
- Capability/applicability explanations, multi-select plan construction, evidence-backed recommendations, user plan edits/exclusions, and exact approval before execution.
- Existing Python/pytest test execution in an isolated worker.
- OpenAPI-based API checks against an exact authorized target, subject to verified adapter availability and target policy.
- Deterministic evaluation, audit/provenance, cancellation, restart recovery, per-domain reports, and one consolidated report.
- AI-off workflow; configured local model may provide bounded advisory help only after explicit configuration and schema validation.
- Security/isolation proof gate and a published verified support matrix.

### Excluded from M1 unless separately approved

- Native Windows executable installer, hosted service, multi-tenant operation, REST API, and web UI.
- Any claim of safe arbitrary hostile-code execution.
- Automatic test edits, patching/fix mode, commits, or writes to the user's source tree.
- Unverified language/framework adapters; mobile/device, browser E2E, database, CI/CD mutation, active security testing, fuzzing, performance/load, and destructive checks.
- Remote AI provider enabled by default; mandatory AI dependency; AI-owned verdicts.
- Automatic execution of recommendations or policy expansion from config, model output, project files, API specifications, MCP, or generic confirmation flags.

## 4. Epics and implementation backlog

### EPIC 0 — M1 scope, decisions, and requirement traceability

| ID | Priority | Work item | Dependencies | Acceptance criteria | SRS/plan trace |
|---|---|---|---|---|---|
| ASTA-001 | P0 | Create an M1 requirement-to-work-item ledger | None | Every in-scope SRS requirement maps to a backlog item and verification artifact; exclusions are marked Later/Out of Scope; no SRS ID is silently dropped. | `TRACEABILITY_MATRIX.md`; Gate A |
| ASTA-002 | P0 | Record approved M1 technical defaults and remaining implementation decisions as ADRs | ASTA-001 | Confirmed decisions are distinguished from proposed tools; exact API adapter versions, resource defaults, retention, schema fields, archive caps, and installation details remain explicit release/design decisions with owners. | `ADR_REGISTER.md`; Gate A |
| ASTA-003 | P0 | Freeze M1 support matrix and trust claims | ASTA-001, ASTA-002 | Publish exact Windows/WSL2/Docker/ASTA-Python/pytest/API-adapter combinations only after verification; state trusted/authorized project execution limitation until isolation proof passes. | `NFR-COMP-001`, `NFR-COMP-002`, `NFR-LIC-001`; Compatibility policy |

### EPIC 1 — Reproducible Windows + WSL2 + Docker developer environment

| ID | Priority | Work item | Dependencies | Acceptance criteria | SRS/plan trace |
|---|---|---|---|---|---|
| ASTA-010 | P0 | Define the supported local development setup | ASTA-002 | Setup guide gives tested Windows and WSL2 prerequisites, Linux distribution recommendation, Docker Desktop WSL2 setup, repository location, Python 3.14 setup, and diagnostic commands; unsupported prerequisite produces actionable guidance. | `NFR-COMP-001`; Gate A/D |
| ASTA-011 | P0 | Reproducible dependency and tool inventory | ASTA-010 | ASTA runtime dependencies are pinned/locked; tool and adapter metadata records exact version, source, license, OS/runtime, and update policy; clean environment can reproduce the declared environment. | `NFR-MAINT-001`, `NFR-LIC-001`; Compatibility policy |
| ASTA-012 | P1 | Define container image lifecycle and provenance | ASTA-010, ASTA-011 | Worker image is versioned and reproducible; image update is separate from target project; image/tool versions appear in run evidence; no implicit image pull/execution occurs without the configured policy. | `FR-EXEC-001`, `NFR-SEC-001`; Gate B/C |

### EPIC 2 — CLI contract and input/configuration

| ID | Priority | Work item | Dependencies | Acceptance criteria | SRS/plan trace |
|---|---|---|---|---|---|
| ASTA-020 | P0 | Specify CLI commands, prompts, exit codes, and output locations | ASTA-001 | CLI contract supports intake/inspect, plan/review, approve, run, status, cancel, report, and supported rerun/recovery journey; help text documents flags and exit codes; commands cannot bypass policy. Final command spellings are reviewed before implementation. | `IF-CLI-001`–`IF-CLI-004`; UC-01–UC-06 |
| ASTA-021 | P0 | Define and validate versioned `asta.toml` schema | ASTA-020 | Unknown/invalid fields and invalid types fail before side effects with field-level errors; config cannot reduce hard safety policy; CLI > config > built-in precedence is deterministic; schema version and migration behavior are explicit. | `IF-CFG-001`–`IF-CFG-003`; Gate B |
| ASTA-022 | P1 | Implement multi-channel scope input normalization | ASTA-020, ASTA-021 | Multi-select works from flags/prompts, TOML, and natural-language request; aliases map to versioned canonical IDs; domains/tags are preserved; ambiguous/unsupported labels are clarified or visibly unsupported; no recommendation becomes selected implicitly. | `IF-CLI-002`, `IF-CFG-001`, `FR-SCOPE-003`–`FR-SCOPE-008` |
| ASTA-023 | P1 | Define CLI confirmation and approval interaction | ASTA-020, ASTA-022 | User sees exact target, selected checks, excluded/blocked/unsupported checks, risk, limits, and plan revision; approval is explicit per run/plan revision; generic `--yes` cannot authorize protected checks or bypass missing authorization. | `IF-CLI-003`–`IF-CLI-004`, `FR-PLAN-001`–`FR-PLAN-006`, `FR-SCOPE-001`–`FR-SCOPE-002` |

### EPIC 3 — Project intake, inspection, and capabilities

| ID | Priority | Work item | Dependencies | Acceptance criteria | SRS/plan trace |
|---|---|---|---|---|---|
| ASTA-030 | P0 | Implement local-folder project intake and provenance | ASTA-020, ASTA-021 | Intake canonicalizes path, records source/revision where available, rejects unsupported/malformed input before execution, and does not mutate source; project ownership/authorization confirmation is captured. | `FR-PROJ-001`–`FR-PROJ-005` |
| ASTA-031 | P0 | Implement safe static project inspection | ASTA-030 | Detects Python manifests, pytest config/tests, OpenAPI descriptions, and supported signals without importing/executing project modules; every fact has evidence; unknown remains unknown. | `FR-INS-001`–`FR-INS-007`; Taxonomy registry |
| ASTA-032 | P0 | Register initial capability set and applicability states | ASTA-031 | Only verified Python/pytest and API capabilities may be executable; states distinguish `Applicable`, `Not applicable`, `Unsupported`, `Blocked`, `Awaiting authorization`; reasons/prerequisites are reported; project signals do not authorize execution. | `FR-SCOPE-003`–`FR-SCOPE-008`; Capability registry |
| ASTA-033 | P1 | Implement safe archive intake only if archive source is enabled in M1 | ASTA-030 | If archive intake is included, extraction is into an isolated workspace and rejects traversal, symlinks/devices, excessive expansion, and unsafe paths under approved caps; otherwise report archives as unsupported. | `FR-PROJ-002`; Gate C |

### EPIC 4 — Taxonomy, planner, recommendations, and approvals

| ID | Priority | Work item | Dependencies | Acceptance criteria | SRS/plan trace |
|---|---|---|---|---|---|
| ASTA-040 | P0 | Implement versioned normalized taxonomy model | ASTA-022 | Preserve separate dimensions: test level/strategy, domain, protocol/platform, technique, validation intent; one check can carry multiple tags; stable IDs/alias policy are versioned before persisted runs. | `FR-SCOPE-003`–`FR-SCOPE-008`; Taxonomy §1–2 |
| ASTA-041 | P0 | Implement deterministic planner within user-approved scope | ASTA-032, ASTA-040 | Planner uses evidence and adapter manifests; classifies applicability; does not create out-of-scope execution; distinguishes included, excluded, blocked, unsupported, not applicable, pending recommendation. | `FR-PLAN-001`–`FR-PLAN-006` |
| ASTA-042 | P0 | Implement recommendation review and exact approval binding | ASTA-041 | Each recommendation includes rationale/evidence/risk/prerequisites; approved additions bind to run, exact scope, plan revision/content hash and policy version; declined/pending additions never execute; material change invalidates approval and is audited. | `FR-PLAN-004`–`FR-PLAN-006`, `FR-SCOPE-002`; ADR-003 |
| ASTA-043 | P1 | Implement language-boundary decision per check | ASTA-032, ASTA-041 | White-box unit checks require the target module language and compatible runtime/build ecosystem unless a verified binding says otherwise; black-box API checks may use another supported test language against isolated target; component/integration must declare white-box or black-box; no silent substitution. | `FR-GEN-005`–`FR-GEN-007`; ADR-006 |

### EPIC 5 — Persisted workflow, storage, and audit

| ID | Priority | Work item | Dependencies | Acceptance criteria | SRS/plan trace |
|---|---|---|---|---|---|
| ASTA-050 | P0 | Approve physical data contracts and local persistence design | ASTA-001, ASTA-002 | Decide IDs, immutable snapshots, DB schema/migrations, report `schema_version`, artifact digest, file/DB consistency, locking, backup/deletion/retention; record ADRs before persistence implementation. | `DATA_AND_ARTIFACT_CONTRACTS.md` §8; Gate A/B |
| ASTA-051 | P0 | Implement persisted state machine with one active worker | ASTA-050 | State transitions are guarded and persisted; restart resumes/marks run deterministically; concurrent start cannot create conflicting active worker; idempotent cancel/rerun behavior defined; immutable run snapshot preserved. | `FR-EXEC-007`–`FR-EXEC-010`, `NFR-REL-001`–`NFR-REL-003`; UC-05 |
| ASTA-052 | P0 | Implement audit events for security and lifecycle decisions | ASTA-050, ASTA-051 | Audit target decisions, approvals, plan revisions, egress decisions, credential references, cancellation, AI provider/data-sharing event, and artifact access; no secret values; each decision has actor/source, time, policy version, and reason. | `FR-SCOPE-001`–`FR-SCOPE-002`, `NFR-OBS-001`, `NFR-PRIV-001` |
| ASTA-053 | P1 | Implement scoped per-run credential injection | ASTA-051, ASTA-052 | M1 accepts a named environment reference or interactive secret input; secret exists only for authorized check; host-wide environment is not passed; secret is not stored in config, DB, reports, prompts, logs, or artifacts; absence/mismatch blocks the check. | `FR-SCOPE-006`, `NFR-SEC-005`, `NFR-PRIV-001` |

### EPIC 6 — Adapter contract and initial Python/pytest adapter

| ID | Priority | Work item | Dependencies | Acceptance criteria | SRS/plan trace |
|---|---|---|---|---|---|
| ASTA-060 | P0 | Approve adapter manifest and output schemas | ASTA-002, ASTA-040, ASTA-050 | Manifest includes stable `adapter_id`, capabilities/tags, applicability evidence, support state, risk, prerequisites, tool/version/license, OS/runtime, allowlisted command/input, output schema, evidence mapping, limits, unsupported conditions. | `FR-GEN-001`–`FR-GEN-007`; Gate B |
| ASTA-061 | P0 | Implement existing pytest execution adapter | ASTA-060, ASTA-051, ASTA-053 | Runs only explicit approved test command in isolated worker; captures exit/stdout/stderr/timing/tool version and raw evidence; does not modify source; missing runtime/prerequisite is `Blocked` or `Unsupported`; adapter does not assign overall verdict. | `FR-EXEC-001`–`FR-EXEC-006`; Taxonomy adapter matrix |
| ASTA-062 | P0 | Implement OpenAPI API-check adapter | ASTA-060, ASTA-051, ASTA-053, ASTA-070 | Supports only approved OpenAPI version(s) and exact authorized target; reject spec URLs/redirects that expand scope; HTTPX transport and Schemathesis use only if version/license/parser are verified; request rate, timeout, redaction, and output caps enforced; preserves request/response/schema provenance. | `FR-GEN-001`–`FR-GEN-007`, `FR-EXEC-001`–`FR-EXEC-006`; API taxonomy |
| ASTA-063 | P1 | Map adapter output into canonical attempt states | ASTA-061, ASTA-062, ASTA-080 | Output parser is schema validated and deterministic; missing oracle becomes `Inconclusive`; missing prerequisite/authorization `Blocked`; unsupported tool/runtime `Unsupported`; malformed output `Error`; each attempt has exactly one canonical status. | `FR-EVAL-001`–`FR-EVAL-006`; Data contracts §3 |

### EPIC 7 — Isolation, egress, resources, and safety release gate

| ID | Priority | Work item | Dependencies | Acceptance criteria | SRS/plan trace |
|---|---|---|---|---|---|
| ASTA-070 | P0 | Implement disposable isolated execution worker | ASTA-010, ASTA-012, ASTA-051 | Worker has no Docker socket, privileged mode, host networking, host home, or host-wide environment; source is read-only; output is separate; non-root where supported; capabilities are reduced; container/process cleanup occurs on every exit. | `FR-EXEC-001`–`FR-EXEC-010`, `NFR-SEC-001`–`NFR-SEC-006`; Gate C |
| ASTA-071 | P0 | Implement deny-by-default egress enforcement | ASTA-070, ASTA-060 | Worker has no network unless the approved check needs it; all requests/redirects and DNS-resolved addresses are rechecked; exact target only; deny localhost/private/link-local/metadata unless explicitly approved; separate approved registry access for dependency-install phase. | `FR-SCOPE-005`–`FR-SCOPE-007`; TM-02–TM-05; Gate C |
| ASTA-072 | P0 | Enforce resource and output limits | ASTA-070 | CPU, memory, process count, disk, output size, wall-clock, and API rate limits are enforced; numerical defaults are approved from representative workload measurements; limit cause is captured as evidence and canonical outcome. | `FR-EXEC-003`–`FR-EXEC-006`, `NFR-PERF-001`–`NFR-PERF-004`; Gate C |
| ASTA-073 | P0 | Verify worker cancellation, timeout, crash recovery, and cleanup | ASTA-051, ASTA-070 | Cancel/timeout/crash stops process group and removes worker/network/temp volumes/credential access; preserves completed attempts and partial evidence; records cleanup success/failure; never reports a false pass. | `FR-EXEC-007`–`FR-EXEC-010`, `NFR-REL-001`–`NFR-REL-003`; Gate C |
| ASTA-074 | P0 | Pass adversarial isolation and target-boundary acceptance suite | ASTA-070–ASTA-073 | Demonstrate host-file/socket denial, no source writes, resource caps, DNS rebinding, direct IPv4/IPv6, redirect, local/private/link-local/metadata denial, target allow case, archive/path attacks if applicable, oversized output, cancellation, cleanup, and secret-canary redaction. If any critical case fails, disable project-code execution and release only read-only analysis/trusted-project mode as documented. | `NFR-SEC-001`–`NFR-SEC-006`; Security proof gate; Gate C |

### EPIC 8 — Deterministic evaluator and traceability/change-aware behavior

| ID | Priority | Work item | Dependencies | Acceptance criteria | SRS/plan trace |
|---|---|---|---|---|---|
| ASTA-080 | P0 | Implement deterministic expectation and result evaluator | ASTA-050, ASTA-063 | Evaluator consumes stored evidence/expectation/policy only; no AI dependency/import; only user criteria, formal specification, existing test, configured threshold, or defined universal check can authoritatively pass/fail; AI-only expectation is `Inconclusive`. | `FR-EVAL-001`–`FR-EVAL-010`; ADR-005 |
| ASTA-081 | P0 | Implement exact retry/flaky/timeout/overall verdict rules | ASTA-080 | Fail then pass retry becomes `Flaky`; preserve all attempts; timeout is `Failed` only for an explicit configured timeout assertion, otherwise `Error`; overall verdict exactly follows contract; no pass if required evidence persistence/reporting fails. | Evaluator golden contract; `DATA_AND_ARTIFACT_CONTRACTS.md` §3 |
| ASTA-082 | P1 | Implement source revision and change-impact traceability where available | ASTA-030, ASTA-031, ASTA-050 | Store source revision/hash and links among requirements, checks, attempts, findings, evidence, and reports; unchanged scope may reuse evidence only when compatibility/freshness is proven; changed target/plan invalidates approval; unsupported change analysis is clearly `not measured`. | `FR-INS-006`, `FR-AN-001`–`FR-AN-002`, `FR-REP-001`–`FR-REP-009` |

### EPIC 9 — Reporting, artifacts, and user review

| ID | Priority | Work item | Dependencies | Acceptance criteria | SRS/plan trace |
|---|---|---|---|---|---|
| ASTA-090 | P0 | Approve report JSON schema and artifact contract | ASTA-050, ASTA-063, ASTA-080 | Define exact `schema_version`, field names, timestamps, enums, nullability, redaction metadata, artifact digest, compatibility evolution; validate before report implementation. | `DATA_AND_ARTIFACT_CONTRACTS.md` §§5–8; Gate B |
| ASTA-091 | P0 | Compose one report for each selected domain and one consolidated report | ASTA-090, ASTA-080 | Multi-domain run emits every selected domain report plus one consolidated report; counts/verdicts reconcile; include target/scope, environment, timing, plan, expectations/provenance, adapter/tool versions, all dispositions, evidence links, limitations, recommendations, and tested-scope qualification. | `FR-REP-001`–`FR-REP-009`; ADR-004 |
| ASTA-092 | P0 | Write Markdown and versioned JSON reports safely | ASTA-090, ASTA-091 | Markdown is readable; JSON validates against approved schema; artifact IDs resolve safely; hashes/provenance checked; secrets redacted; malicious text/HTML and traversal are safely handled; missing/corrupt artifact is explicit. | `FR-REP-001`–`FR-REP-009`; Gate C/D |
| ASTA-093 | P1 | Add conditional JUnit XML output for pytest-compatible CI use | ASTA-091 | Emit only if status/finding mapping is validated; retain canonical JSON/Markdown as authoritative; document unsupported mapping; CLI exit code matches documented run verdict policy. | `IF-CLI-001`, `FR-REP-008`; Release acceptance |

### EPIC 10 — AI gateway and natural-language assistance

| ID | Priority | Work item | Dependencies | Acceptance criteria | SRS/plan trace |
|---|---|---|---|---|---|
| ASTA-100 | P0 | Ensure complete supported AI-off workflow | ASTA-020–ASTA-093 relevant prerequisites | Intake, inspect, plan, approve, run, evaluate, report, cancel/recover do not require a model; missing/unconfigured model cannot block deterministic supported workflow. | `FR-AI-001`–`FR-AI-007`; UC-06 |
| ASTA-101 | P1 | Add bounded local-model gateway only after provider is configured | ASTA-100, ASTA-052 | Local provider is off by default; explicit config required; bounded inputs/output, schema validation, timeout/retry caps, provenance and opt-in audit; model cannot execute commands, alter scope, approve, change policy, or set verdict; invalid/unavailable provider degrades safely. | `FR-AI-001`–`FR-AI-007`; ADR-005, ADR-015 |
| ASTA-102 | P1 | Implement natural-language selection normalization and confirmation | ASTA-022, ASTA-041 | Request is converted into proposed canonical selections; user reviews final plan; ambiguous intent asks clarification; unavailable AI uses deterministic parsing or reports unsupported; AI suggestions remain recommendations until exact approval. | `IF-CLI-002`–`IF-CLI-004`, `FR-SCOPE-003`–`FR-PLAN-006` |

### EPIC 11 — Release acceptance, evidence, and support claims

| ID | Priority | Work item | Dependencies | Acceptance criteria | SRS/plan trace |
|---|---|---|---|---|---|
| ASTA-110 | P0 | Build representative Python/API bug-garden fixtures | ASTA-061–ASTA-063, ASTA-080 | Controlled fixtures include known passing/failing tests, API contract cases, missing oracle, unsupported combination, and flaky/retry behavior; benchmark answer keys are not exposed to planner/worker. No numeric recall threshold is claimed until approved. | Verification Plan §§5–6; Gate D |
| ASTA-111 | P0 | Run full M1 CLI acceptance journey | ASTA-020–ASTA-102 | Demonstrate add/inspect → multi-select plan → recommendations → approval → isolated execution → deterministic evaluation → domain reports + consolidated report → cancel/rerun/recovery. AI-off path succeeds. | UC-01–UC-06; Gate D |
| ASTA-112 | P0 | Close M1 quality, security, compatibility, privacy, and license evidence | ASTA-074, ASTA-091–ASTA-111 | Release package links each claim to build/tool version, environment, requirement ID, evidence, outcome, and limitation; publish supported matrix; unresolved numeric targets and retention are approved or marked release-blocking; no certification/hostile-code claim. | `NFR-*`; Gate A–D |
| ASTA-113 | P0 | Define release install/upgrade/uninstall and data-retention instructions | ASTA-010, ASTA-050, ASTA-112 | Document WSL2 CLI installation, prerequisites, updates/rollback, where state/artifacts live, backup/deletion/retention behavior, and troubleshooting; user can identify and remove ASTA-owned data without deleting project source. | `FR-PROJ-005`, `NFR-USE-001`, operations guide |

## 5. Suggested milestone sequence and release gates

| Milestone | Backlog scope | Exit criteria |
|---|---|---|
| **M0 — Design/contract freeze** | ASTA-001–003, ASTA-020, ASTA-021, ASTA-040, ASTA-050, ASTA-060, ASTA-090; resolve numeric limits, schema and trust assumptions | Gate A and B pass. SRS traceability complete for M1; no ambiguity about authority, approval, data, worker boundary, output schemas, or supported scope. |
| **M1a — Safe skeleton** | ASTA-010–012, ASTA-020–023, ASTA-030–032, ASTA-040–043, ASTA-050–053 | CLI can intake/inspect/plan/review and persist state with AI off; no test project code runs yet. Config errors and missing authority have no side effects. |
| **M1b — Isolated pytest vertical slice** | ASTA-060–061, ASTA-063, ASTA-070–074, ASTA-080–081 | A known Python fixture can run approved pytest in the worker and produce deterministic statuses; isolation Gate C passes before execution is exposed as supported. |
| **M1c — API checks and reports** | ASTA-062, ASTA-071–072, ASTA-082, ASTA-090–093 | Authorized OpenAPI API check runs through approved target policy; Markdown/JSON domain and consolidated reports validate and redact data. |
| **M1d — M1 release candidate** | ASTA-100–113 | Full journey and reliability/security/compatibility evidence passes; M1 support matrix, install guide, limitations, and release claims approved. |

**Release rule:** If the execution isolation/egress gate fails, do not ship project-code execution as enabled. Ship only a clearly labeled read-only analysis/plan/report capability if that mode independently meets its acceptance criteria; otherwise block M1 release.

## 6. Cross-cutting quality gates

1. **Requirements/design readiness:** requirement IDs mapped; decisions recorded; approved support claims; schema and security boundaries reviewed.
2. **Component contracts:** invalid config has no side effects; adapter manifests and input/output schemas validate; approval freshness is enforced; evaluator goldens are deterministic.
3. **Safe execution:** deny-by-default network, exact target checks, read-only source, resource limits, no arbitrary commands, scoped secrets, cleanup on all exits, attack fixtures pass.
4. **Release acceptance:** full CLI journey; AI-off path; report reconciliation; restart/cancel/rerun; benchmark evidence; documented support and limitations.

No numeric latency, throughput, availability/SLA, archive maximum, project size, concurrency beyond one worker, severity scale, coverage/mutation threshold, benchmark threshold, retention duration, or resource-limit values are invented in this backlog. Approve measurable values in M0/M1b before using them as release claims.

## 7. Risks and mitigations

| Risk | Impact | Backlog response |
|---|---|---|
| WSL2/Docker container boundary is weaker than the trust claim needed | Unsafe execution or misleading product claim | Limit M1 to authorized/trusted projects while proving the boundary; fail closed; consider stronger isolation or ECI only after licensing/platform analysis. |
| Windows/WSL2/Docker Desktop versions and editions differ | Setup and security behavior vary by environment | Verify and publish a narrow support matrix; test setup detection; do not assume Docker Desktop licensing is free for all users. |
| API specification or redirects expand target scope | SSRF or unauthorized testing | Treat specs as untrusted input; bind approved target; validate each redirect and resolved address at egress. |
| Secrets leak into worker output, reports, or AI | Credential compromise | Per-run scoped injection, minimize collection, redact before persistence, canary-secret tests, AI off by default. |
| No authoritative test oracle | False confidence or inaccurate verdict | `Inconclusive` when expectation is AI-only/unsupported; evaluator is deterministic and reports tested scope and gaps. |
| Tool versions/licenses/platform vary | Broken adapter or redistribution exposure | Per-adapter inventory, license review, pinned versions, verified support tuple; do not enable unverified tools. |
| Large M1 scope dilutes security and usability | Late release or unsafe shortcuts | Keep browser/mobile/database/active security/performance/fix mode outside M1; gate the core vertical slice first. |

## 8. Decisions still required during backlog refinement

Approval of the defaults resolves the product direction, but these engineering values still need evidence or a recorded ADR before the dependent implementation/release gate:

- Exact Python patch and dependency versions; exact pytest, HTTPX, Schemathesis versions, license, supported OpenAPI versions, commands, and output mapping.
- Exact WSL distribution/version policy and tested Windows editions/builds; Docker Desktop licensing expectations and whether ECI is optional or required for any deployment claim.
- CLI command spellings, exit-code mapping, final `asta.toml` schema and canonical test-ID/alias versioning.
- Numeric CPU, memory, process, disk, output, timeout, API-rate, archive and project-size limits based on representative workloads.
- Credential input UX (environment reference vs interactive prompt), exact variable naming, and whether to defer OS keyring integration entirely for M1.
- SQLite physical schema/migrations, artifact hash algorithm/layout, report JSON fields, timestamp format, retention/deletion/backup, and crash-consistency behavior.
- OpenAPI 3.0/3.1 support selection; whether Schemathesis is enabled for M1 or API checks start with deterministic HTTPX contract assertions only.
- Whether JUnit XML is included in M1 and precise mapping of ASTA states to JUnit outcomes.
- Whether archive intake is M1; if included, exact expansion/path/file-size caps.
- Security benchmark cases and the minimum evidence that permits project-code execution; threat boundary and allowed private-target rules.
- Exact release quality thresholds, bug-garden benchmark measures, severity scale, dependency vulnerability policy, and retention periods.

## 9. Definition of backlog completion

This backlog is ready to schedule when each P0 has an owner, estimate, and dependency review; M0 decisions have ADRs; and every in-scope SRS requirement has a work item and verification artifact. Implementation begins only after the user explicitly starts that phase.
