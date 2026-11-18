# ASTA Architecture Decision Record Register

**Status:** Initial decision register  
**Authority:** Product decisions in [`PRD.md`](PRD.md), normative requirements in [`SRS.md`](SRS.md), architecture proposals in [`TAD.md`](TAD.md)

## 1. Decision status vocabulary

- **Confirmed:** Explicitly agreed in project discussion or recorded as a locked product constraint in the baseline.
- **Proposed:** Recommended architecture/technology, not yet selected as binding implementation technology.
- **Open:** Requires stakeholder choice or evidence before the dependent release.
- **Superseded:** Replaced by a later approved ADR; retain history.

This register distinguishes product commitments from technical suggestions. A candidate library or framework in the TAD is not a confirmed stack choice.

## 2. Confirmed decisions and constraints

### ADR-001 — Local-first installed product with agent workflow and MCP integration

- **Status:** Confirmed product direction.
- **Decision:** ASTA is a locally installed, user-directed testing application with an agent workflow and an MCP integration option. The CLI is the first interface. MCP exposes shared application services.
- **Reason:** The product needs a dependable local workflow with user review/approval, while remaining usable by agent hosts.
- **Constraint:** MCP is an integration surface, not a second testing engine and cannot bypass scope, approvals, risk controls, or evaluator rules.
- **Open detail:** Installation format and supported operating systems are TBD; a Windows `.exe` has not been selected as the required distribution format.

### ADR-002 — Multi-select test scope

- **Status:** Confirmed.
- **Decision:** A user may request multiple testing types for one plan/run. The system normalizes requested labels to canonical, versioned capability IDs and preserves domain tags.
- **Constraint:** Automatic applicability resolution may filter/classify checks inside approved scope; it cannot silently add recommendations to the run.

### ADR-003 — Recommendations require exact user approval

- **Status:** Confirmed.
- **Decision:** The agent may recommend additional tests with evidence and rationale. The user must approve the exact additions before they execute.
- **Constraint:** Recommendation approval binds to the run, scope, plan revision, and content hash. Material plan/scope change invalidates affected approval.

### ADR-004 — Individual domain reports plus one consolidated report

- **Status:** Confirmed.
- **Decision:** A run selecting multiple domains produces an individual report for every selected domain and one consolidated report that includes the overall scope, statuses, evidence, gaps, and limitations.

### ADR-005 — Deterministic verdicts; AI is advisory

- **Status:** Confirmed.
- **Decision:** Deterministic application code evaluates evidence against explicit expectations. AI may assist analysis, planning, bounded generation, and explanations but cannot set execution scope, authorization, evaluator rules, or final pass/fail statuses.
- **Constraint:** AI-only expectations produce `Inconclusive`; the evaluator does not import or call an AI provider. AI-off operation remains available for supported deterministic paths.

### ADR-006 — Explicit language boundary

- **Status:** Confirmed.
- **Decision:** White-box unit tests use the target module language and a compatible runtime/build ecosystem unless an adapter explicitly declares a supported binding. Black-box API/E2E/UI/performance tests may use another supported test language against an isolated running target. Component/integration checks declare white-box or black-box before language binding.
- **Constraint:** No silent language substitution.

### ADR-007 — Approved scope, risk classes, and safe execution

- **Status:** Confirmed security/product constraints.
- **Decision:** No network by default; exact target/action/risk is checked before execution and before every worker network request. The worker has bounded resources, read-only source, separate run workspace, and cleanup on every exit.
- **Constraint:** Safe checks are the proposed production default; writes, destructive checks, active security checks, and high-traffic checks require exact per-check authorization and limits. If the isolation boundary is unavailable or unproven, untrusted execution is disabled; read-only analysis or trusted projects only may be allowed as configured.
- **Caveat:** Docker is a candidate sandbox, not a claim of hostile-code containment by itself.

### ADR-008 — No source modification by default

- **Status:** Confirmed constraint.
- **Decision:** Generated tests/artifacts live outside the target source tree by default. Optional fix mode is later scope, disabled by default, separately authorized, uses a separate copy/branch, displays a patch, and reruns relevant checks.

### ADR-009 — Shared core with phased interfaces

- **Status:** Confirmed release direction.
- **Decision:** CLI is M1; MCP is a shared-service integration in M1/M2; REST API and React web UI are M3 candidates. All interfaces use the same core use cases and policy gates.

## 3. Proposed decisions requiring evidence or approval

### ADR-010 — Python modular monolith for initial core

- **Status:** Proposed in TAD; not binding.
- **Proposal:** Python modular monolith with explicit boundaries for CLI, workflow, adapters, evaluator, and persistence.
- **Rationale to validate:** Fits candidate Python project adapters and local workflow; fewer operational parts for a one-machine product.
- **Evidence needed:** Supported target language matrix, packaging/OS proof, dependency/security review, adapter API prototype.

### ADR-011 — CLI framework and configuration parser

- **Status:** Proposed/open.
- **Candidates:** Typer CLI; `.testagent.yaml` declarative project config with a strict schema.
- **Decision needed:** Exact package command name, CLI parser/framework, schema/validation library, and config precedence details.

### ADR-012 — Durable workflow implementation

- **Status:** Proposed/open.
- **Proposal:** Persisted Python state machine initially; evaluate LangGraph only if branching/checkpointing needs warrant it.
- **Decision needed:** Concrete persistence and concurrency semantics, idempotency key, resume behavior, lock ownership, and crash-recovery policy.

### ADR-013 — Local persistence and artifacts

- **Status:** Proposed/open.
- **Candidates:** SQLite for project/run/plan/result/audit records; local content-addressed artifact files; SQLAlchemy/Alembic only if ORM/migrations are justified; PostgreSQL/object storage later if deployment needs require it.
- **Decision needed:** Selected schema/migration strategy, artifact hashing algorithm, atomicity across DB/files, backup, deletion, retention, and encryption behavior.

### ADR-014 — Sandbox and operating-system baseline

- **Status:** Proposed/open and security-critical.
- **Candidates:** Docker, rootless where supported, strict egress controls. Windows+WSL2/Docker versus Linux is not settled.
- **Decision needed:** Supported OS/runtime and threat model evidence demonstrating isolation, egress, cleanup, filesystem, and resource-control guarantees. Until evidence passes, restrict execution per ADR-007.

### ADR-015 — AI provider and model policy

- **Status:** Proposed/open.
- **Proposal:** Local Ollama first; remote OpenAI-compatible providers optional and off unless explicit project opt-in; all calls through one bounded/schema-validated gateway.
- **Decision needed:** Model, hardware requirements, license, quality/latency/memory thresholds, endpoint allowlist, data disclosure UX, and remote retention terms.

### ADR-016 — Later REST API and web interface stack

- **Status:** Proposed/open; M3.
- **Candidates:** FastAPI + Pydantic; React + TypeScript + Vite.
- **Decision needed:** Authentication/token lifecycle, network binding, role model, origin/CSRF policy, artifact access controls, and production hosting boundary.

### ADR-017 — Adapter tools and supported matrix

- **Status:** Proposed/open.
- **Candidates:** Playwright, axe-core, Schemathesis, pytest/HTTPX, Semgrep, Bandit, Gitleaks, pip-audit, OSV-Scanner, OWASP ZAP, Locust, plus project-native runners.
- **Decision needed:** Exact versions, licenses, platform compatibility, command invocations, output parsers, update policy, and security review for each selected adapter.

### ADR-018 — Initial product support and thresholds

- **Status:** Open.
- **Decision needed:** Initial source languages/frameworks and OS support, archive caps, severity scale, coverage/mutation thresholds, defect benchmark threshold, retry/flaky policy, performance limits, latency/concurrency targets, retention, privacy, and distribution claims.

## 4. Explicitly rejected or prohibited alternatives

These are constraints from the current product baseline, not inferred technology preferences:

- **AI-only final verdict:** Rejected; model output alone cannot produce `Passed` or `Failed`.
- **Implicit execution of recommendations:** Rejected; exact recommended checks need user approval.
- **Policy bypass through a UI, API, MCP, config, or generic `yes` flag:** Prohibited; no interface may grant its own authorization or override policy.
- **Arbitrary shell commands from model output:** Prohibited; scripts/commands must come from validated adapters, approved plan, and structured generation.
- **Network access by default:** Prohibited; deny by default and allow only approved egress.
- **Writing into tested source by default:** Rejected; separate artifact/work area unless a later explicitly approved fix operation applies.
- **Unrestricted active security, destructive, or high-volume checks:** Prohibited without authorization and configured limits.
- **Claiming all languages/environments or hostile-code safety from Docker alone:** Prohibited; support and isolation claims require evidence.

The project has not explicitly rejected a particular database, cloud provider, programming language, CI vendor, or commercial deployment model. Do not add those to the rejected list unless a future decision records them.

## 5. ADR change template

```text
ADR-NNN — <decision title>
Status: Proposed | Confirmed | Rejected | Superseded
Date / owner:
Context:
Decision:
Alternatives considered:
Rationale and evidence:
Consequences / security impact:
Affected PRD/SRS/TAD sections and requirement IDs:
Review trigger:
```

