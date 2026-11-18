# ASTA Data and Artifact Contracts

**Status:** Logical contract draft; physical database and JSON schema are not selected  
**Sources:** [`SRS.md`](SRS.md) §§7, 10–11; [`TAD.md`](TAD.md) §§4, 10–11  
**Related:** [`ADR_REGISTER.md`](ADR_REGISTER.md), [`FAILURE_RECOVERY_AND_STATE_MODEL.md`](FAILURE_RECOVERY_AND_STATE_MODEL.md)

## 1. Contract status and invariants

This document refines SRS entity requirements into a logical contract. It does not declare an implemented SQLite schema, endpoint payload, ORM, or field nullability unless explicitly stated. SQLite, local content-addressed artifacts, SQLAlchemy/Alembic, and an OS keyring/encrypted secret store are proposals; final choices remain open.

Invariants:

1. Every run stores a snapshot of scope, capabilities, limits, policy, retention, plan revision, and available source revision. Later project/config edits do not rewrite it.
2. Every plan/check/approval refers to stable identifiers and the exact revisions/content it covers.
3. Every attempt has exactly one status from the attempt enum; retries create new attempts and preserve old evidence.
4. Evaluator output is reproducible from stored evidence, expectation, and policy without a new model call.
5. Secret values never appear in normal project/plan/run/finding/report records. Only a scoped `CredentialReference` is persisted.
6. Artifacts have a stable ID, content hash, type, provenance, redaction state, and run/check relationship. Missing/corrupt evidence is explicit, not silently dropped.
7. A report has `schema_version`; exact versioning/compatibility policy must be decided before implementation.

## 2. Logical entities and minimum fields

| Entity | Minimum logical fields (SRS baseline) | Relationship/invariant |
|---|---|---|
| `Project` | Name, source/reference, detected type/profile, settings, retention | Owns targets, requirements, plans, runs, and credential references. Record source type, revision/snapshot when available, created time, and settings. |
| `Target` | URL/host/path, environment, authorization record, allowed scope | Belongs to project; exact target/action/environment is checked before execution and each network request. |
| `Requirement` | User story, acceptance criterion, expected outcome, provenance | Expectation source is explicit; never treat a model-only expectation as authoritative. |
| `TestPlan` | Version, state, creator/source, explanation, timestamps | Contains checks. Plan approval is tied to exact run/scope/plan revision/content hash. |
| `TestCase` / `Check` | Key, target, capability/tags, purpose, risk, prerequisites, expectation/source, adapter, limits, script version | Includes explicit applicability/execution reason and adapter/tool version; duplicate only when target+operation+assertion equivalent. |
| `Run` | Plan/config snapshot, state, timing, environment, revision | Binds approvals and immutable run configuration snapshot. |
| `TestExecution` / `Attempt` | Attempt number, status, observations, reason, duration | Belongs to run/check; owns artifact references; retries preserve previous attempts. |
| `Finding` | Severity, title, expected/actual where known, reproduction, source, confidence, signature | Links evidence, source/provenance, and one or more attempts. Severity scale remains TBD. |
| `Artifact` | Type, hash, location/reference, redaction state/time | Linked to run/execution/finding; local content-addressed file storage is proposed. Never expose raw secret values. |
| `CredentialReference` | Secret-store pointer, purpose, allowed targets/actions | No secret value in DB/config/report. Secret store choice is TBD. |
| `ProviderConfiguration` | Provider, model, endpoint, credential reference, sharing policy | Secret is a reference; remote calls require explicit project opt-in and an audit event. |
| `Approval` | Approved item/class, actor, time, scope, policy version | Must include exact check/run/revision/hash/decision/limits sufficient to validate freshness. |
| `AuditEvent` | Event type, run/project/component IDs, actor/source, timestamp, decision, reason, policy version | At minimum audit approvals, target decisions, AI data-sharing calls, egress decisions, cancellations, and artifact access. Secret-redacted. |

Recommended implementation metadata such as `created_at`, `updated_at`, UUID format, foreign-key strategy, and concurrency version are to be decided in physical data-model ADR; they are not currently fixed fields beyond the SRS terms above.

## 3. Enumerations and lifecycle values

### 3.1 Attempt status (exactly one)

```text
Passed | Failed | Flaky | Skipped | Blocked | Inconclusive | Unsupported | Error
```

Rules: failure followed by pass is `Flaky`; timeout is `Failed` only when an explicit configured timeout assertion is violated, otherwise `Error`; missing oracle/criteria yields `Inconclusive`; missing prerequisite/authorization remains explicit. These are not interchangeable with capability or run states.

### 3.2 Overall verdict

```text
Failures found         = any attempt/check is Failed
Unreliable results     = no Failed, but at least one Flaky or Error
Passed in tested scope = at least one Passed and no Failed/Flaky/Error
No result              = otherwise
```

Always include tested scope, status counts, gaps, and limitations. Never imply the entire project is bug-free, secure, compliant, or release-ready.

### 3.3 Quality disposition (separate from attempt status)

```text
Accepted | Needs review | Rejected
```

Disposition evaluates suite/check quality (execution plus assertion quality, coverage where supported, repeatability, mutation evidence, duplicates, fixture determinism, and configured thresholds). Missing measurements are `not measured`, never zero/pass.

### 3.4 Plan, run, attempt, and finding states

TAD lifecycle proposal:

```text
Plan:    Draft → Awaiting review → Approved → Superseded or Executed
Run:     Queued → Inspecting → Planning → Awaiting approval → Generating
         → Running → Evaluating → Reporting → Completed
         | Cancelled | Failed | Blocked | Partial
Attempt: Created → Running → Completed(status)
Finding: New → Reviewed → Accepted / Rejected / Deferred / Resolved
```

This state list is the architecture baseline. Exact transition guards, terminal-state definitions, persisted event schema, and whether `Partial` is terminal require approval in the workflow implementation design. A cancellation preserves completed attempts/evidence; unstarted checks are `Skipped`; run is `Cancelled` as stated in SRS use cases.

### 3.5 Capability/applicability states

```text
Applicable | Not applicable | Unsupported | Blocked | Awaiting authorization
```

Reports additionally distinguish `Pending`, `Declined`, and `Not measured`; these are planning/report dispositions, not attempt statuses. Exact cross-enum schemas should use separate fields rather than one overloaded status.

## 4. Expectation and provenance contract

Each check records expected outcome/assertion and exactly which source supports it:

```text
user criteria | formal specification | existing test | configured threshold
| defined universal check | AI-inferred
```

Only the first five categories can authoritatively produce `Passed`/`Failed`. An AI-inferred expectation is advisory and yields `Inconclusive` unless later supported by an authoritative source. Detected project facts include evidence source and confidence where implemented. Store adapter, tool version, script version, source/revision, target, limits, and policy version needed for replay.

## 5. Artifact contract

### Artifact metadata (logical minimum)

| Attribute | Requirement |
|---|---|
| Artifact ID | Stable opaque reference; format TBD. |
| Type | Script, log, trace, screenshot, response, report, coverage/measurement, or other declared evidence type. |
| Content digest | Hash of stored bytes; algorithm TBD. Content-addressed storage is proposed. |
| Run/check/attempt references | Identify the producer and relevant check; preserve provenance. |
| Producer metadata | Adapter ID/version, tool version, script version, capture time where available. |
| Redaction | State/time and redaction policy version; secrets must be redacted before persistence. |
| Storage reference | Local content-addressed file path/URI proposal; physical layout and access control TBD. |
| Retention/deletion | Apply project/run policy; duration and backup behavior TBD. |
| Validation | Validate type, size, path, hash, and safe rendering/download behavior. |

Never trust artifact file names as paths. Report references resolve by ID/hash, not raw project-controlled path. If artifact is missing, corrupt, withheld, or redacted, report the limitation explicitly.

## 6. Human and machine report contract outline

M1 report formats: Markdown and versioned JSON. M3 candidate formats: HTML, JUnit XML, and SARIF for compatible security findings. Each run creates one report per selected domain and one consolidated report.

Required report content from the SRS:

- `schema_version` in machine-readable JSON;
- project/source/revision provenance where available;
- declared target, scope, environment, policy and timing;
- plan/check list, expectation source, adapter/tool/script versions;
- all attempt statuses/counts and overall verdict, including gaps;
- findings with severity, title, expected/actual where known, reproduction steps, evidence, source type, and confidence where applicable;
- non-executed dispositions: `Pending`, `Declined`, `Unsupported`, `Not applicable`, `Blocked`, `Awaiting authorization`, `Not measured`;
- evidence references, redaction/limitations, recommendations, and clear statement that result is limited to tested scope.

The exact JSON schema, field names, nullable rules, severity enum, timestamp format, and backward-compatibility policy remain open; define and version them before M1 implementation.

## 7. Persistence and consistency requirements

- Proposed: SQLite for local relational records; local content-addressed artifact files; PostgreSQL/object storage only as later options; secrets in OS keyring or selected encrypted store.
- Preserve run state and completed attempt evidence across restart.
- Persist enough plan/script/tool/evidence/expectation data to replay without another model call.
- DB/file atomicity, crash recovery, backup/restore, encryption, retention duration, and deletion of backup copies are unresolved.
- Deletion scope in the current TAD covers project rows, artifacts, prompts, replies, and scripts under the approved retention policy.
- Do not mark a run `Completed` while required persistence/report steps failed; use an explicit partial/error outcome per the final transition contract.

## 8. Physical schema and payload approval checklist

Before writing migrations or API implementations, approve: identifier format; schema versioning; unique keys; foreign keys; immutable versus mutable records; approval binding/hash canonicalization; timestamp/time-zone format; enum evolution; artifact hash/storage design; secret references; retention/deletion/backup behavior; SQLite concurrency and one-worker locking; migration tooling; JSON report schema; and API request/response/error schemas. Record these decisions in ADRs and test their invariants at the storage boundary.

