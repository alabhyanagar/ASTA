# ASTA Interface and Workflow Specification

**Status:** Workflow baseline; detailed CLI syntax/contracts remain partly open  
**Related:** [`PRD.md`](PRD.md) §§5–7, 10; [`SRS.md`](SRS.md) §§4–5, 9–10; [`TAD.md`](TAD.md) §§4–5, 12

## 1. Interface contract principles

- CLI, MCP, and later REST/UI are thin interfaces over shared application services. There is one scope resolver, planner, approval service, workflow coordinator, adapter registry, evaluator, and report composer.
- No interface may grant its own authorization, bypass the execution policy, or turn a recommendation into an approved check.
- Every interface exposes the same canonical test IDs, applicability states, risk classes, run states, and evaluator results.
- Invalid requests/configuration fail before side effects and provide actionable field/reason information.
- The CLI remains the dependable approval path because MCP host interaction capabilities differ.

## 2. Scope selection and resolution

### 2.1 Accepted selection channels

1. **CLI flags/prompts:** user supplies one or more canonical IDs or aliases.
2. **Project configuration:** `.testagent.yaml` may define requested scope, language/framework hints, options, resource limits, retention, AI/data-sharing settings, and approvals where implemented.
3. **Natural language:** a later/proposed parsing path may infer requested types. It must resolve to the same normalized scope model and show the interpreted selection for confirmation where ambiguity/risk requires it. It is not authorization.

### 2.2 Precedence and hard ceiling

TAD suggested precedence, from highest to lowest:

1. Runtime security policy (hard ceiling; cannot be broadened by user config).
2. Explicit per-run user selection.
3. Project defaults.
4. Reusable profile defaults.

Natural-language inference is an input candidate and must not override an explicit safer choice or grant approval. Conflicts are shown and resolved before plan generation.

### 2.3 Resolution outcomes

For every requested or considered check, show one of the exact capability states:

- `Applicable`
- `Not applicable`
- `Unsupported`
- `Blocked`
- `Awaiting authorization`

Include reason, evidence/prerequisite, adapter/version, risk, and whether it is requested or only recommended. A recommendation is a separate proposed item, not an implicitly selected capability.

## 3. Primary CLI workflow (M1)

Candidate commands recorded in the TAD/SRS:

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

The exact executable name, full option syntax, stable exit-code table, interactive prompts, and shell completion remain TBD. SRS command operations are: `project add`, `inspect`, `plan`, `approve`, `run`, `status`, `cancel`, `rerun`, and `report`.

### 3.1 End-to-end flow

1. **Intake:** choose local folder, archive, public Git repository, or authorized running URL where enabled. Validate before extraction/network access. Record provenance and requested target scope.
2. **Inspect:** deterministic inspection detects supported languages/frameworks, manifests, test commands, dependencies, API specs/routes, and deployment signals. Unknown stays unknown; static inspection does not execute/import project modules.
3. **Select:** user chooses multiple test types. Normalize aliases to canonical IDs and show detected capabilities, applicability, prerequisites, risk, expected oracle, and limitations.
4. **Recommend:** ASTA may propose additional checks with evidence and rationale. Each addition remains Pending until the user explicitly approves the exact check(s). Declined items are recorded and do not execute.
5. **Plan:** generate a versioned plan with target, test level/protocol/platform/technique dimensions, adapter/tool versions, expectation source, resource ceilings, and included/excluded/blocked reasons.
6. **Review/edit:** user may edit, approve, or exclude checks. The approval records actor, timestamp, plan/scope revision, content hash, and policy version. Any material change invalidates affected approvals.
7. **Risk approval:** checks in `Needs approval`, `Destructive`, `Active security`, or `High traffic` require separate exact per-check approval and limits. The proposed production default is Safe-class only; this is not yet a finalized production-policy decision.
8. **Execute:** coordinator schedules approved checks only; worker rechecks target/scope before each network request; output and resources are bounded; credentials are scoped.
9. **Evaluate:** deterministic evaluator assigns exactly one attempt status and computes the overall run verdict from policy and evidence.
10. **Report:** generate one report per selected test domain plus a consolidated report. Show completed and non-executed checks, gaps, evidence, limitations, provenance, and recommendations.

## 4. CLI behavior and exit contract

### Required observable behaviors

- Multi-select selection must resolve all requested canonical types, not silently stop after one.
- Before execution show exact target, scope manifest summary, check list, applicability, prerequisites, risk, recommendation/approval state, and blocked/unsupported reasons.
- Non-interactive operation stops if required authorization/approval is absent. A generic `--yes` cannot override policy.
- Invalid `.testagent.yaml` fails before project/run side effects and points to the invalid field.
- Human-readable output is required; optional JSON output must be machine-readable and schema/version identified where applicable.
- Stable exit codes are required but their values and mapping are TBD. They must distinguish at least successful completion, findings/failure, blocked/approval needed, unsupported/configuration error, cancellation, and internal error before CLI release.

## 5. Configuration contract

`.testagent.yaml` is a proposed configuration file, required by SRS IF-CFG-001 for the baseline. The exact schema/version and default values remain TBD. It covers, where implemented:

- selected scope and enabled capabilities;
- language/framework hints and adapter-specific options;
- resource limits and target authorization/scope references;
- retention settings;
- AI mode, provider/model, and data-sharing settings;
- approvals where the implementation supports declarative records.

Configuration expresses intent but cannot widen runtime policy. Secret values must not be embedded in ordinary config; use secret-store references. The SRS contains illustrative—not approved default—values `max_context_tokens: 12000`, timeout `300` seconds, retries `3`, line coverage `70`, branch coverage `60`.

Validation requirements: schema/version validation; unknown-field policy decided before implementation; type/range/enum checks; adapter-specific validation; cross-field checks; field-level error; no side effects on invalid config; persist an immutable run snapshot so later edits cannot rewrite a past run.

## 6. Approval semantics

Approval is explicit, scoped, revision-bound, and auditable. At minimum record:

- actor/approval source and timestamp;
- exact run, scope, plan revision, check ID(s), target/action and risk class;
- content hash and policy version;
- decision (`Approved`/`Declined`) and any limits/conditions;
- invalidation reason if scope/plan/target changes.

An approval for a plan does not substitute for a required per-check risk approval. Recommendation approval covers only the specified recommendations. A declined/pending check remains non-executable and visible in report outputs.

## 7. MCP interface

MCP (SRS `IF-MCP-001`, Should, M1/M2) exposes shared application operations; it does not implement a second engine. TAD examples include:

- project inspection;
- plan creation and retrieval;
- approval recording, subject to host/user confirmation;
- run start/status/cancel;
- report/evidence retrieval.

MCP schemas, resource/prompt exposure, trust/identity mapping, user-confirmation behavior, and host-specific limits are not finalized. MCP calls must pass the same policy/approval checks as CLI. If the MCP host cannot provide required human confirmation, operation must stop and direct the user to the CLI or another dependable approval path.

## 8. REST API and web UI (M3 candidates only)

The following are proposed TAD routes, not locked API contracts:

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

Authentication proposal: local single-user token. Token creation/storage/rotation, network binding, authorization roles, CSRF/CORS/origin controls, and download access policy require a separate approved API security design before M3.

The M3 React UI candidate covers intake, profile review, plan review, approvals, progress, cancellation, findings, artifacts, history, and comparisons. It must expose scope and status without requiring raw log inspection and should support keyboard navigation, semantic labels, and readable status indicators.

## 9. Report output contract

M1 formats: human-readable Markdown and versioned JSON. Later candidates: HTML, JUnit XML, SARIF for compatible security findings. The output set for one run includes each selected domain’s report and one consolidated report. Reports show scope, environment, timing, plan, all statuses/counts, findings, evidence, expectation/source provenance, limitations, recommendations, and non-executed outcomes. Machine formats include `schema_version`; exact JSON fields are documented in [`DATA_AND_ARTIFACT_CONTRACTS.md`](DATA_AND_ARTIFACT_CONTRACTS.md).

