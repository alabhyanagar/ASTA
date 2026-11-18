# Software Requirements Specification
## Autonomous Software Testing Platform (ASTA)

**Document ID:** ASTA-SRS-001  
**Version:** 1.0  
**Status:** Baseline for product development  
**Date:** 2026-11-18  
**Related documents:** [PRD](PRD.md) · [TAD](TAD.md)  
**Implementation status:** Not started

## 1. Introduction

### 1.1 Purpose

This specification defines requirements for ASTA: a locally installable, user-directed testing application with an agent workflow and MCP integration option. It accepts a codebase or authorized running target, identifies supported checks, creates reviewable plans, generates/configures tests through adapters, executes approved checks in isolated workers, evaluates evidence deterministically, and reports results, gaps, and limitations.

### 1.2 Conventions

**Shall** means mandatory; **should** means recommended; **may** means optional. Priority: **Must** is a core/product contract; **Should** is accepted but can be phased; **Later** is accepted future scope. Phase labels: **M1** foundation/CLI, **M2** AI and core adapters, **M3** API/UI and deeper analysis, **Later** expansion. Proposed technology values are not binding decisions unless expressly marked selected.

Each requirement has an ID, priority, phase, and verification evidence. Numerical thresholds marked TBD require stakeholder approval before release acceptance.

### 1.3 Scope

The product shall inspect project evidence, allow the user to select multiple testing types, select applicable checks only within that approved scope, explain untested scope, run approved checks safely, and return reproducible evidence-backed results. The user controls scope; recommendations are not authorization.

### 1.4 Intended audience

Product owner, developers, testers/QA, security reviewers, platform operators, adapter authors, and stakeholders approving scope/risk.

### 1.5 Terms

| Term | Definition |
|---|---|
| Agent | Planning/analysis behavior that may use bounded AI. |
| Worker | Controlled process/container that executes checks. |
| Evaluator | Deterministic status assignment from evidence, expectation, and policy. |
| Check | Planned testing action with target, expectation source, assertion, risk, and limits. |
| Attempt | One execution of a check; retries create new attempts. |
| Expectation/oracle | Approved criterion or rule used to compare observed behavior. |
| AI-inferred expectation | Model-suggested outcome not confirmed by user, formal specification, accepted project test, or approved threshold. |
| Test garden | Application with known planted defects used to measure product detection behavior. |

## 2. Overall product requirements

### 2.1 Goals

- Reduce manual effort to find and run relevant tests.
- Generate/configure reproducible tests from project files, specs, API schemas, and user workflows.
- Produce evidence-based outcomes and expose uncertainty/uncovered scope.
- Provide prioritized findings with practical improvement suggestions.
- Add adapters without coupling tools to the core evaluator.
- Protect source, credentials, data, and targets.

### 2.2 Success measures

Thresholds are TBD. Candidate metrics: defect recall, false positives, duplicate findings, flaky rate, Blocked/Unsupported/Inconclusive accuracy, reproducibility, execution time, AI-on versus AI-off quality/runtime, and security/privacy proof points.

### 2.3 Out of scope

- Guaranteeing software is bug-free, secure, compliant, or suitable for release.
- Replacing human acceptance testing, usability research, accessibility expert review, or professional penetration testing.
- Unrestricted security/destructive/high-volume load tests without authorization.
- Supporting every language/framework/OS/device/database initially.
- Changing original application source by default.

## 3. Actors and operating environment

| Actor | Responsibilities / constraints |
|---|---|
| Project owner/developer | Submits project, defines scope, reviews failures/suggestions, decides rerun or patch. |
| Tester/QA | Supplies criteria, workflows, constraints, thresholds, test accounts; reviews plans/findings. |
| Administrator | Configures providers, execution policy, storage, retention, integrations; multi-user role model TBD. |
| Testing agent | Inspects/plans/generates/explains; cannot approve scope or assign pass status. |
| Execution worker | Runs approved checks and captures evidence; obeys scope, approvals, timeout/resource limits. |
| External services | AI provider, source control, browser, scanner, CI, database when configured; optional and explicit. |

Initial environment is a single developer workstation, CLI-first, local storage, one worker, and Docker-proposed execution. Supported OS (Windows+WSL2/Docker, Linux, macOS), hardware, and container runtime remain TBD.

## 4. External interface requirements

### 4.1 CLI

- **IF-CLI-001 (Must, M1):** CLI shall provide `project add`, `inspect`, `plan`, `approve`, `run`, `status`, `cancel`, `rerun`, and `report` operations. **Verify:** scripted end-to-end run uses documented commands and exit codes.
- **IF-CLI-002 (Must, M1):** CLI shall support multi-select testing types and readable plus optional JSON output. **Verify:** multi-type run resolves all requested canonical types.
- **IF-CLI-003 (Must, M1):** CLI shall show scope, applicability, prerequisites, risk, recommendations, approvals, and blocked/unsupported reasons before execution. **Verify:** CLI fixtures show all decision states.
- **IF-CLI-004 (Must, M1):** Non-interactive operation shall stop if required authorization/approval is absent; a generic yes flag cannot override policy. **Verify:** no worker starts in missing-approval fixture.

Illustrative command names; exact package/product command name remains TBD:

```text
testagent project add
testagent inspect
testagent plan
testagent approve
testagent run --types unit,integration,api,regression
testagent status
testagent cancel
testagent rerun
testagent report
```

### 4.2 Configuration

- **IF-CFG-001 (Must, M1):** Project shall support declarative `.testagent.yaml` for scope, enabled capabilities, options, languages/frameworks, resource limits, retention, AI mode/data sharing, and approvals where implemented. **Verify:** schema validation and persisted run snapshot.
- **IF-CFG-002 (Must, M1):** Invalid configuration shall fail before side effects with field-level explanation. **Verify:** invalid fields create no run.
- **IF-CFG-003 (Must, M1):** Configuration cannot broaden runtime safety policy. **Verify:** policy conflict fixture remains blocked.

Illustrative values from the project discussion (not approved defaults): `max_context_tokens: 12000`, timeout `300` seconds, retries `3`, line coverage `70`, branch coverage `60`.

### 4.3 MCP, REST API, and web UI

- **IF-MCP-001 (Should, M1/M2):** MCP shall expose shared application operations; it shall not implement a second engine or bypass policy. **Verify:** equivalent CLI/MCP request produces equivalent plan/evaluation.
- **IF-API-001 (Should, M3):** REST API shall expose versioned project, target, inspection, plan, approval, run, cancellation, rerun, finding, artifact, and report operations. **Verify:** contract tests for schemas, auth, and errors.
- **IF-UI-001 (Should, M3):** Web UI shall support intake, profile review, plan review, approvals, progress, cancellation, findings, artifacts, history, and comparisons. **Verify:** browser acceptance run completes and opens report.
- **IF-API-002 (Should, M3):** API shall validate requests before side effects and return documented errors. **Verify:** invalid request returns field errors and creates no run.

Candidate versioned routes (proposal; not binding until API design approval):

```text
POST /api/v1/projects; GET/DELETE /api/v1/projects/{id}
POST /api/v1/projects/{id}/targets
POST /api/v1/projects/{id}/inspections
POST /api/v1/projects/{id}/plans; PATCH /api/v1/plans/{id}
POST /api/v1/plans/{id}/approvals
POST /api/v1/runs; GET /api/v1/runs/{id}
POST /api/v1/runs/{id}/cancel; POST /api/v1/runs/{id}/rerun
GET /api/v1/runs/{id}/executions; GET /api/v1/findings
GET /api/v1/artifacts/{id}; GET /api/v1/runs/{id}/report?format=...
```

Authentication proposal: local token for single-user use. Token creation, storage, rotation, network binding, and roles are TBD.

### 4.4 External tools and software interfaces

Candidate tools: project-native runner; Playwright; axe-core; Schemathesis; pytest/HTTPX; static analysis/security/dependency tools; Locust; OWASP ZAP; local Ollama. Exact versions, licenses, commands, platform support, and output parsers require verification. Each adapter shall record its ID, tool/version/license, and evidence mapping.

## 5. Functional requirements

### 5.1 Project intake and lifecycle

- **FR-PROJ-001 (Must, M1):** Create project from enabled local folder, archive, public Git repository, or authorized running URL. **Verify:** enabled intake fixtures create project; unsupported inputs return clear error.
- **FR-PROJ-002 (Must, M1):** Record source type/reference, detected profile, revision/snapshot when available, created time, and settings. **Verify:** project and report show provenance.
- **FR-PROJ-003 (Must, M1):** Validate archives and reject traversal paths, unsafe links, device files, and size/file-count/expansion-limit violations. **Verify:** adversarial archive fixtures are rejected without writing outside workspace.
- **FR-PROJ-004 (Should, M1):** Support inspect, update, archive, and delete subject to retention policy. **Verify:** each operation has documented outcome and audit.
- **FR-PROJ-005 (Should, Later):** Support authenticated private repositories via credential references. **Verify:** secret values absent from project records.

### 5.2 Scope, authorization, and risk

- **FR-SCOPE-001 (Must, M1):** Maintain an authorization manifest listing allowed hosts, URLs/paths, environments, actions, and authorization record. **Verify:** manifest attaches to each plan/run.
- **FR-SCOPE-002 (Must, M1):** Check scope before plan approval, before execution, and before every worker network request. **Verify:** out-of-scope host, redirect, IP, and changed-manifest fixtures are blocked/logged.
- **FR-SCOPE-003 (Must, M1):** Support user-selected multi-select types; automatic applicability resolution shall operate only inside approved scope. **Verify:** resolver cannot add pending recommendations to run.
- **FR-SCOPE-004 (Must, M1):** Recommend extra tests with evidence and rationale; require explicit approval of exact additions before execution. **Verify:** pending/declined recommendation does not run.
- **FR-SCOPE-005 (Must, M1):** Classify checks by risk and enforce risk approval table in §9. **Verify:** each risk class is blocked without required approval.
- **FR-SCOPE-006 (Must, M1):** Store secret values outside ordinary project/plan/run/report records and pass only scoped references or short-lived access. **Verify:** canary secret absent in database/reports.
- **FR-SCOPE-007 (Must, M1):** Redact recognized secrets before logs, model inputs, reports, and artifacts are persisted. **Verify:** canary-secret tests cover output paths.
- **FR-SCOPE-008 (Must, M1):** Distinguish `Applicable`, `Not applicable`, `Unsupported`, `Blocked`, and `Awaiting authorization`; explain reasons. **Verify:** state fixtures and report output.

### 5.3 Inspection and capability detection

- **FR-INS-001 (Must, M1):** Detect supported languages, frameworks, manifests, build/test commands, and dependencies using deterministic rules. **Verify:** known samples yield expected facts; unknown remains unknown.
- **FR-INS-002 (Must, M1):** Discover supported routes, API specs, test files, and deployment configuration. **Verify:** fixtures with/without OpenAPI, routes, tests, and Docker config classify correctly.
- **FR-INS-003 (Should, M2):** Record evidence source and confidence for material profile facts. **Verify:** every material fact points to a file/signal/command or unknown.
- **FR-INS-004 (Must, M1):** Capability registry evaluates each adapter against required signals and returns state/reason. **Verify:** positive and negative fixtures return expected applicability.
- **FR-INS-005 (Must, M1):** Avoid duplicate execution when checks share target, operation, and assertion; retain all report tags. **Verify:** equivalent plan checks share key and execute once.
- **FR-INS-006 (Must, M1):** Static analysis shall not execute/import project modules. **Verify:** hostile initialization fixture is not run during inspection.
- **FR-INS-007 (Should, M3):** Map source changes to likely affected checks with confidence and full-suite option. **Verify:** change fixture shows impacted and uncertain mapping.

### 5.4 Planning and approval

- **FR-PLAN-001 (Must, M1):** Create project-specific plan from profile, registry, scope, requirements, and limits. **Verify:** plan contains only in-scope checks supported by installed adapters.
- **FR-PLAN-002 (Must, M1):** Each check records target, capability/tags, purpose, prerequisites, risk, limits, expected outcome, and expectation source. **Verify:** schema rejects missing mandatory fields.
- **FR-PLAN-003 (Must, M1):** Distinguish user criteria, formal specs, existing tests, thresholds, universal checks, and AI-inferred expectations. **Verify:** each assertion displays provenance.
- **FR-PLAN-004 (Must, M1):** Explain included, excluded, blocked, unsupported, not-applicable, or awaiting-authorization capabilities. **Verify:** plan export includes reason for each relevant capability.
- **FR-PLAN-005 (Must, M1):** Allow user to review, edit, approve, or exclude checks. **Verify:** unapproved checks cannot run.
- **FR-PLAN-006 (Must, M1):** Tie approval to run, exact scope/plan revision, and content hash; material changes invalidate approval. **Verify:** modified plan requires new approval.

### 5.5 Generation and language boundary

- **FR-GEN-001 (Must, M1):** Prefer project-native tests, formal schemas, or deterministic generators when they cover the check. **Verify:** schema fixture chooses deterministic generation.
- **FR-GEN-002 (Must, M2):** Generate/configure scripts from approved plans and version scripts linked to checks/runs. **Verify:** every execution identifies script version.
- **FR-GEN-003 (Must, M2):** Parse/validate generated scripts, require at least one meaningful assertion, and reject out-of-scope targets. **Verify:** malformed, assertion-free, out-of-scope scripts rejected.
- **FR-GEN-004 (Must, M1):** Store generated tests outside tested source tree unless source changes explicitly authorized. **Verify:** normal run leaves source-tree hash unchanged.
- **FR-GEN-005 (Should, Later):** Generate synthetic data from formal schemas/user constraints. **Verify:** generated data validates to schema and labeled synthetic.
- **FR-GEN-006 (Must, M1):** Enforce white-box unit tests use target module language/compatible ecosystem; black-box API/E2E/performance may use another supported language against isolated running target. **Verify:** incompatible unit selection blocked; cross-language black-box test requires available adapter/target.
- **FR-GEN-007 (Must, M1):** Component/integration scenario declares white-box or black-box before language binding. **Verify:** ambiguous scenario cannot advance without classification.

### 5.6 Execution and job control

- **FR-EXEC-001 (Must, M1):** Execute project code/scripts through worker boundary with time, memory, CPU, process, disk, and output limits. **Verify:** runaway fixture terminated within configured ceiling.
- **FR-EXEC-002 (Must, M1):** Worker mounts source read-only and writes to separate run workspace unless approved operation says otherwise. **Verify:** normal test cannot modify source.
- **FR-EXEC-003 (Must, M1):** Worker has no network by default and only validated authorized egress for approved check. **Verify:** denied hosts unreachable, authorized target reachable.
- **FR-EXEC-004 (Must, M1):** Separate dependency installation from test execution and limit install phase to approved package sources. **Verify:** separate phase/network policies recorded.
- **FR-EXEC-005 (Must, M1):** If isolation unavailable, disable untrusted execution and explain; allow configured read-only analysis. **Verify:** no sandbox runtime means no worker execution.
- **FR-EXEC-006 (Must, M1):** User can cancel queued/active run; record cancellation and retain partial evidence. **Verify:** worker stops, unstarted checks Skipped, run Cancelled.
- **FR-EXEC-007 (Should, M1):** Persist state and recover/mark interrupted work after worker crash/restart. **Verify:** crash yields no false Passed.
- **FR-EXEC-008 (Must, M1):** Initial deployment supports one worker per machine and configured concurrency bound. **Verify:** worker limit enforced and recorded.
- **FR-EXEC-009 (Must, M1):** Cleanup resources, credentials, and network on every exit path. **Verify:** success/failure/timeout/cancel cleanup evidence.
- **FR-EXEC-010 (Must, M1):** Active security, destructive, and high-traffic checks require exact targets, type-specific authorization, and limits. **Verify:** risk fixtures block without approvals.

### 5.7 Evaluation and statuses

- **FR-EVAL-001 (Must, M1):** Assign exactly one attempt status: `Passed`, `Failed`, `Flaky`, `Skipped`, `Blocked`, `Inconclusive`, `Unsupported`, or `Error`. **Verify:** golden cases cover each status.
- **FR-EVAL-002 (Must, M1):** Evaluator shall be deterministic for identical stored evidence, expectations, and policy. **Verify:** replay returns identical status and explanation.
- **FR-EVAL-003 (Must, M1):** Only user criteria, formal specs, existing tests, configured thresholds, or defined universal checks can produce Passed/Failed. AI-only expectations produce Inconclusive. **Verify:** AI-only oracle fixture cannot pass/fail.
- **FR-EVAL-004 (Must, M1):** Evaluator shall not call/import an AI provider/module. **Verify:** dependency/import-boundary check.
- **FR-EVAL-005 (Must, M1):** Preserve retry attempts; failure followed by pass yields Flaky. **Verify:** mixed attempt fixture.
- **FR-EVAL-006 (Must, M1):** Timeout is Failed only if it violates configured timeout assertion; otherwise Error. **Verify:** timeout golden cases.
- **FR-EVAL-007 (Must, M1):** Overall verdict limited to declared scope; show counts for every status and gaps. **Verify:** report never claims bug-free/security/safe.
- **FR-EVAL-008 (Must, M1):** Run verdict rules: Failures found if any Failed; Unreliable results if none Failed but any Flaky or Error; Passed in tested scope if at least one Passed and no Failed/Flaky/Error; otherwise No result. **Verify:** run golden cases cover each branch.
- **FR-EVAL-009 (Must, M1):** Keep quality disposition separate from attempt status: Accepted / Needs review / Rejected. **Verify:** report/API shows separate fields.
- **FR-EVAL-010 (Must, M1):** Unmeasured coverage/mutation is “not measured,” never zero/pass. **Verify:** no-parser fixture.

### 5.8 AI, analysis, and recommendations

- **FR-AI-001 (Must, M2):** Every model call goes through gateway with task, bounded input, output schema; returns validated data/refusal/error. **Verify:** mock provider responses are schema validated.
- **FR-AI-002 (Must, M2):** AI-off mode preserves rule-based planning, deterministic generation, execution, evaluation, and reporting. **Verify:** supported full run with AI disabled.
- **FR-AI-003 (Should, Later):** Remote compatible providers supported only when enabled per project; local Ollama proposed first. **Verify:** no remote call absent opt-in.
- **FR-AI-004 (Must, M2):** Invalid output gets bounded configurable retries then fallback/degraded state. **Verify:** malformed/rate-limited response.
- **FR-AI-005 (Must, M2):** Repository/docs/page/test content is untrusted; AI cannot change target, scope, approvals, evaluator rules, or evidence. **Verify:** prompt-injection fixtures.
- **FR-AI-006 (Must, M2):** Remote AI use discloses selected content and records provider/model/task/data-sharing choice/outcome. **Verify:** audit log and opt-in.
- **FR-AI-007 (Should, M3):** AI claims cite evidence ID, label inferred/confirmed, and include confidence or unknown. **Verify:** invalid evidence references rejected/omitted.
- **FR-AN-001 (Should, M3):** Group matching findings while preserving contributing execution/tool evidence. **Verify:** merged finding retains references.
- **FR-AN-002 (Should, M3):** Compare runs by revision/plan/config and classify added/resolved/changed/unchanged findings. **Verify:** comparison fixture.

### 5.9 Reports and artifacts

- **FR-REP-001 (Must, M1):** Generate human report with scope, environment, timing, plan, status counts, findings, evidence, limitations, recommendations. **Verify:** report section fixture.
- **FR-REP-002 (Must, M1):** Generate versioned JSON report schema. **Verify:** schema validation includes `schema_version`.
- **FR-REP-003 (Should, M3):** Generate HTML/JUnit XML and SARIF for compatible security findings. **Verify:** enabled exports validate; unsupported format not offered.
- **FR-REP-004 (Must, M1):** Retain logs, scripts, tool versions, screenshots, traces, responses, and required evidence subject to redaction/retention. **Verify:** every evidence reference resolves or explains absence.
- **FR-REP-005 (Must, M1):** Finding includes severity, title, expected/actual where known, reproduction steps, evidence, source type, confidence where applicable. **Verify:** unsupported finding without evidence/explanation rejected.
- **FR-REP-006 (Must, M1):** Distinguish deterministic findings, user-confirmed expectations, and AI-inferred suggestions. **Verify:** UI/export labels each source.
- **FR-REP-007 (Must, M1):** Produce individual report for every selected domain and one consolidated report. **Verify:** multi-domain run produces both forms and links evidence.
- **FR-REP-008 (Must, M1):** Reports distinguish Pending, Declined, Unsupported, Not applicable, Blocked, Awaiting authorization, Not measured, and executed statuses. **Verify:** report fixtures.
- **FR-REP-009 (Should, M3):** Access-check report/artifact downloads in API/UI. **Verify:** authorized access succeeds; unauthorized denied.

### 5.10 Configuration and optional fix mode

- **FR-CONF-001 (Must, M1):** Store run configuration snapshot for scope, capabilities, limits, policy, and retention; later edits do not rewrite it. **Verify:** persisted snapshot replay.
- **FR-CONF-002 (Should, M2):** Configure provider/model/AI mode/data-sharing policy and audit settings. **Verify:** validation and audit.
- **FR-CONF-003 (Should, Later):** Fix mode disabled by default and requires explicit authorization. **Verify:** no patch without enablement and approval.
- **FR-CONF-004 (Should, Later):** Fix mode works on separate copy/branch, displays patch, and reruns relevant checks. **Verify:** original checkout unchanged; patch/evidence downloadable.
- **FR-CONF-005 (Should, Later):** Multi-user roles may follow local single-user release. **Verify:** role authorization tests before declaration.

## 6. Testing capability catalog and applicability

| Signal | May enable | Limits/prerequisites |
|---|---|---|
| OpenAPI/Swagger or reachable schema | REST contract/schema, auth/regression | Weak/no oracle yields Inconclusive. |
| Reachable/startable web app | Navigation, forms, responsive, accessibility, screenshots, frontend performance | Business flows need user criteria. |
| Existing tests and runnable commands | Existing test suites and coverage | Requires supported runtime/command. |
| Supported language/manifests | Static analysis, lint, secrets, dependency tools | Adapter/platform support required. |
| Dockerfile/compose | Later static container/config checks | Do not assume safe runtime config. |
| Database URL and migrations | Database checks | Disposable database and supplied authorization. |
| Android package and emulator | Android checks | Emulator/device adapter available. |
| Workload profile and explicit approval | Bounded performance run | Rate/users/duration limits required. |

## 7. Data requirements

| Entity | Minimum information |
|---|---|
| Project | Name, source/reference, detected type/profile, settings, retention; owns targets, requirements, plans, runs, credential refs. |
| Target | URL/host/path, environment, authorization record, allowed scope. |
| Requirement | User story, acceptance criterion, expected outcome, provenance. |
| TestPlan | Version, state, creator/source, explanation, timestamps; contains checks. |
| TestCase/Check | Key, target, capability/tags, purpose, risk, prerequisites, expectation/source, adapter, limits, script version. |
| Run | Plan/config snapshot, state, timing, environment, revision. |
| TestExecution/Attempt | Attempt number, status, observations, reason, duration; owns artifacts. |
| Finding | Severity, title, expected/actual, reproduction, source, confidence, signature. |
| Artifact | Type, hash, location, redaction state/time; linked to run/execution/finding. |
| CredentialReference | Secret-store pointer, purpose, allowed targets; never secret value. |
| ProviderConfiguration | Provider, model, endpoint, credential reference, sharing policy. |
| Approval | Approved item/class, actor, time, scope, policy version. |

Initial storage proposal: SQLite plus local content-addressed artifacts; SQLAlchemy/Alembic candidate; PostgreSQL/object store later. Secrets outside DB via OS keyring or selected encrypted store. Retention/encryption TBD.

## 8. Non-functional requirements

### 8.1 Security and privacy

- **NFR-SEC-001 (Must):** Untrusted code executes only in isolated worker; if boundary unavailable, disable execution and explain.
- **NFR-SEC-002 (Must):** Deny network by default and enforce approved egress allowlists.
- **NFR-SEC-003 (Must):** Protect credentials in transit/at rest using selected mechanisms; exact encryption TBD.
- **NFR-SEC-004 (Must):** Redact secrets before persistence/service of logs/reports/artifacts.
- **NFR-SEC-005 (Must):** Prevent prompt injection or model output from changing target/scope/approval/evaluator.
- **NFR-SEC-006 (Must):** Validate archive paths/expansion, target redirects/addresses/metadata, artifact paths/content, and dependency-install boundary.
- **NFR-PRIV-001 (Must):** Disclose/minimize project content sent remotely; remote calls disabled absent opt-in; preview selected content.
- **NFR-PRIV-002 (Must):** Enforce configurable retention/deletion for source, prompts, replies, evidence, reports; exact durations TBD.

### 8.2 Reliability, reproducibility, and performance

- **NFR-REL-001 (Must):** Persist run state and completed attempt evidence across restart.
- **NFR-REL-002 (Must):** Identical evidence, expectations, and evaluator policy yield identical status.
- **NFR-REL-003 (Must):** Support bounded cancellation/worker termination and cleanup.
- **NFR-PERF-001 (Must):** Enforce configurable CPU/memory/process/output/wall-clock limit per check.
- **NFR-PERF-002 (Should):** Measure planning, queue, execution, and report durations separately.
- **NFR-PERF-003 (Should):** Performance reports include workload/environment/ceilings and qualify same-host metrics.
- **NFR-SCALE-001 (Must):** One worker per machine with bounded concurrency initially.
- **NFR-SCALE-002 (Later):** Permit multiple workers/alternate storage without changing evaluator semantics.
- **NFR-PERF-004 (TBD):** Inspection/planning/report/artifact/concurrency targets must be set before production.

### 8.3 Usability, maintenance, observability, compliance

- **NFR-USE-001 (Should):** UI exposes scope, plan state, progress, and status without requiring raw log inspection.
- **NFR-USE-002 (Should):** UI supports keyboard navigation, semantic labels, readable status indicators.
- **NFR-MAINT-001 (Must):** Adapter declares ID, capabilities, version, license, applicability, and risk class.
- **NFR-MAINT-002 (Must):** Evaluator/reporter/sandbox do not import or call AI module.
- **NFR-OBS-001 (Must):** Structured logs carry run/component IDs and redact secrets.
- **NFR-COMP-001 (Must):** Publish verified OS/project-type support per release.
- **NFR-LIC-001 (Must):** Review exact integrated tool/model licenses before distribution/hosting.
- **NFR-COMP-002 (Must):** Automated compliance checks shall not be represented as legal/regulatory certification.

## 9. Risk classes and approvals

| Class | Examples | Approval rule |
|---|---|---|
| Safe | Static analysis on source copy, project tests in sandbox, read-only requests, passive scans | May run after plan approval if scope allows. |
| Needs approval | Writes on non-disposable target, real credentials, database access | Approve each check. |
| Destructive | Delete/change data, migrations/rollback, fault injection | Per-check approval; disposable target only. |
| Active security | Active scans/fuzzing against target | Per-check approval; target in manifest. |
| High traffic | Load/stress/spike/endurance | Per-check approval with rate, user, duration ceilings. |

Proposed production default is Safe-class checks only. Exceptions require explicit per-check approval and audit; final production policy remains TBD.

## 10. Use cases

### UC-01 Create project and inspect

Actor: owner. Preconditions: accessible source or authorized URL. Flow: choose intake, provide source/scope, system validates and inspects, displays facts/confidence/gaps. Alternate: unsupported project/unknown commands become Unsupported/Blocked. Postcondition: project and inspection exist.

### UC-02 Generate and approve plan

Actor: tester/owner. Preconditions: profile and scope exist. Flow: registry checks adapters, planner creates checks with expectation source/risk/limits, user edits/approves/excludes; high-risk checks await separate approval. Postcondition: versioned plan and approval record.

### UC-03 Execute run

Actor: owner/CLI user. Preconditions: approved plan, isolation/test data, risk approvals. Flow: runner queues, worker executes, artifacts redacted/stored, evaluator assigns status, report generated. Alternate: missing setup Blocked; unsupported adapter Unsupported; crash Error. Postcondition: all attempts persisted.

### UC-04 Review findings

Actor: developer/tester. Flow: inspect counts/findings, reproduction/evidence, suggestions, confirm expectation for future run. Annotations may be saved; original evidence remains immutable.

### UC-05 Cancel or rerun

Actor: owner. Cancel active run or choose checks to rerun; all prior attempts and audit history preserved.

### UC-06 AI provider unavailable

When provider is unavailable/invalid, gateway records failure, retries within budget, uses rule-based fallback where possible, marks AI degraded; otherwise step becomes Blocked/Error. AI-off run remains available for supported deterministic path.

## 11. Release acceptance criteria

- Supported project can be added, inspected, planned, approved, executed, and reported from CLI.
- End-to-end bug-garden run records plan, scripts/tool versions, attempts, evidence, expectation sources, and report sufficient for replay without new model call.
- Out-of-scope, unauthorized, unsupported, missing prerequisite, absent sandbox, and archive attack cases are handled explicitly.
- Golden evaluator tests cover all statuses, provenance, retry/flaky behavior, timeout classification, and overall verdict rules.
- No result passes solely from model output.
- Network tests prove authorized host reachable and denied hosts, local services, redirects, and metadata endpoints blocked.
- Privacy tests verify source/credential/log/screenshot/remote-call handling and retention behavior.
- Reports include scope, assumptions, every status count, gaps, and evidence; multi-domain report set includes individual and consolidated outputs.
- Benchmark records recall, false positives, duplicates, flaky outcomes, coverage gaps, and runtime; thresholds approved before release.

## 12. Risks and mitigations

| Risk | Mitigation / proof |
|---|---|
| Egress bypass / SSRF | Test direct IP, redirects, IPv6, DNS, metadata, allowed/denied route. |
| Docker insufficient | Trusted-only until isolation proven; do not market as hostile-code safe; assess rootless/VM later. |
| Arbitrary startup variation | Narrow initial supported stack; explicit commands; unsupported startup Blocked. |
| Weak generated tests | Deterministic generators first, assertion validation, AI-off benchmark. |
| Insufficient oracle | Require criteria/contracts; no oracle means Inconclusive. |
| Noisy performance metrics | Require workload/threshold and record environment; same-host results indicative. |
| Source/credential exposure | Local model first, remote opt-in, content preview, redaction, retention, access control. |
| Benchmark answer leakage | Keep answer key outside agent/worker context; score after run. |
| Misleading verdict | Always show scope, counts, gaps, and limits. |

## 13. TBD register

1. Operating system, hardware/RAM/GPU, container runtime; prove Windows+WSL2/Docker or select Linux.
2. Product/package/CLI name.
3. Initial project types/languages; proposal: Python web/API and plain websites.
4. Archive size, file count, and expansion limits.
5. Trusted-only versus validated stronger hostile-code boundary.
6. Retry/flaky policy and numeric coverage/mutation thresholds.
7. Severity scale (candidate Critical/High/Medium/Low/Informational).
8. Benchmark thresholds (e.g. proposed 50% planted API defect recall is unapproved).
9. Local model and license/resource profile; remote AI policy.
10. Artifact/source/prompt/report retention and encryption beyond disk encryption.
11. Product/tool/model licensing and hosted/commercial use.
12. Single/multi-user roles and token lifecycle.
13. Production target policy and per-check approval UX.
14. Performance workload ceilings and timing/concurrency/availability targets.
15. Fix mode/integration timing.

## 14. Traceability and verification methods

| Goal | Requirement groups | Verification |
|---|---|---|
| Relevant checks | FR-INS, FR-SCOPE, FR-PLAN | Sample projects and expected applicability decisions. |
| Reproducible tests | FR-GEN, FR-EXEC, FR-REP | Script review, replay, CLI end-to-end. |
| Evidence-based results | FR-EVAL, FR-REP, NFR-REL | Golden evaluator and report provenance cases. |
| Findings/suggestions | FR-AN, FR-REP, FR-AI | Evidence-link validation and benchmark false positives. |
| Extensible adapters | FR-INS-004/005, NFR-MAINT | Add fake adapter without core change; manifest validation. |
| Safe handling | FR-SCOPE, FR-EXEC, FR-AI, NFR-SEC/PRIV | Scope bypass, network, secret, injection, archive, audit checks. |

Verification methods: **Test** executes checks against criteria; **Inspection** reviews artifacts/config/source; **Analysis** evaluates measurements/evidence; **Demonstration** walks an end-to-end representative use case.

## 15. Proposed technical baseline

| Layer | Candidate | Notes |
|---|---|---|
| Core | Python | Candidate for broad test/security/AI tool integration. |
| CLI | Typer | Candidate; command name TBD. |
| API | FastAPI + Pydantic | Later M3; Django only if administrative needs grow. |
| Database | SQLite, SQLAlchemy, Alembic | PostgreSQL later behind storage abstraction. |
| Job runner | DB-backed job table, one worker | Celery/RabbitMQ only if measured need. |
| Workflow | Persisted Python state machine | Framework only if branching/resume justifies it. |
| Model | Ollama local runtime | Remote compatible provider optional/off by default. |
| Sandbox | Docker, rootless where supported | Egress proxy/firewall proof required; not a hostile-code guarantee. |
| Web | Playwright + axe-core | Visual/cross-browser later. |
| API testing | Schemathesis, pytest, HTTPX | Schema-driven checks first. |
| Security | Semgrep CE, Bandit, Gitleaks, pip-audit, OSV-Scanner, ZAP | Candidate versions/licenses/platform coverage need verification. |
| Performance | Locust | Workload-driven; k6 alternative subject to license review. |
| Web UI | React, TypeScript, Vite | Later release, same core. |
| Reports | Jinja2, JSON, JUnit XML, SARIF | SARIF only where finding semantics map. |
| Artifacts | Local hash-addressed files | Object storage only when scale requires. |

## 16. Glossary

**Adapter:** plugin declaring capability, applicability, risk, tool/version, execution, evidence mapping. **Finding:** reportable defect/concern/observation with evidence. **Flaky:** fails an attempt and passes another; all attempts retained. **Scope manifest:** approved targets/environments/actions available to a run. **Oracle:** expectation source used by evaluator.

