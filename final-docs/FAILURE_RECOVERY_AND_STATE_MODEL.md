# ASTA Failure, Recovery, and State Model

**Status:** Proposed operational contract derived from baseline  
**Sources:** [`SRS.md`](SRS.md) §§5, 9–10; [`TAD.md`](TAD.md) §§4, 10–11  
**Related:** [`DATA_AND_ARTIFACT_CONTRACTS.md`](DATA_AND_ARTIFACT_CONTRACTS.md)

## 1. State domains must stay separate

Do not overload one status field to represent run workflow, capability applicability, attempt result, quality disposition, approval, or finding review.

| Domain | Values |
|---|---|
| Plan lifecycle | `Draft → Awaiting review → Approved → Superseded or Executed` |
| Run lifecycle | `Queued → Inspecting → Planning → Awaiting approval → Generating → Running → Evaluating → Reporting → Completed`; terminal/alternate states: `Cancelled`, `Failed`, `Blocked`, `Partial` |
| Attempt lifecycle | `Created → Running → Completed(status)` |
| Attempt status | `Passed`, `Failed`, `Flaky`, `Skipped`, `Blocked`, `Inconclusive`, `Unsupported`, `Error` |
| Capability/applicability | `Applicable`, `Not applicable`, `Unsupported`, `Blocked`, `Awaiting authorization` |
| Recommendation/approval | Pending/awaiting decision, `Approved`, `Declined`; exact persisted enum is TBD |
| Finding review | `New → Reviewed → Accepted / Rejected / Deferred / Resolved` |
| Suite quality disposition | `Accepted`, `Needs review`, `Rejected` |

The run terminal-state set includes `Partial` in the TAD diagram/state list; its precise criteria and relation to `Completed` need an ADR before implementation. Do not use `Partial` to imply the successfully completed checks all passed.

## 2. Guarded transitions

1. **Intake → Inspecting:** only after source/target syntax and archive checks pass. Invalid configuration/source fails before run side effects.
2. **Planning → Awaiting approval:** persist a versioned plan with check-level scope, risk, prerequisites, expectation source, adapter/tool version, and reasons.
3. **Awaiting approval → Generating:** only if plan and required exact risk approvals are valid for the current scope/plan revision/content hash/policy version.
4. **Generating → Running:** every artifact/command passes schema, target, path, assertion, adapter, and resource validation; worker boundary and target authorization are available.
5. **Running → Evaluating:** all started attempts have terminal records or explicit interruption outcome; evidence is stored/redacted or absence explained.
6. **Evaluating → Reporting:** evaluator runs deterministically from stored evidence and authoritative expectations; no AI import/call.
7. **Reporting → Completed:** required reports/schema and run state persist. If report/persistence cannot complete, use an explicit `Partial`/`Failed` contract rather than claiming complete success; exact rule requires approval.
8. **Any active state → Cancelled:** record actor/time/reason; stop queued/active worker group; unstarted checks `Skipped`; preserve partial evidence and cleanup result.
9. **Any state → Blocked:** only when a policy, approval, target, prerequisite, or isolation gate prevents execution; include actionable reason and whether safe read-only analysis is available.
10. **Any active state → Failed/Error:** unexpected internal/tool/worker failure; preserve diagnostics and completed attempt evidence; never synthesize `Passed`.

## 3. Failure classification

| Condition | Required classification/behavior | User-visible information |
|---|---|---|
| Invalid `.testagent.yaml` or malformed interface request | Validation error before side effects; no run created | Field/path, expected type/range, and correction guidance. |
| User declined recommendation or approval | `Declined`/not executed; run may proceed with remaining approved checks if policy allows | Exact omitted check and decision recorded. |
| Approval absent, stale, wrong plan/target/hash | `Awaiting authorization` or `Blocked`; no worker for that check | Approval scope, stale revision, required action. |
| Unsupported project language/tool/OS | `Unsupported` | Unsupported combination and required adapter/runtime if known. |
| Missing required tool/runtime/test data/schema | `Blocked` if potentially resolvable; no false attempt pass | Missing prerequisite and setup path. |
| Target outside allowlist, unsafe redirect/address, deny-by-default egress | `Blocked` | Target and policy reason, with sensitive data redacted. |
| Isolation runtime absent/unproven | Disable untrusted execution; `Blocked` or read-only analysis only | Explain restriction; do not imply sandboxed execution. |
| Adapter returns invalid/missing evidence | `Error` or `Inconclusive` according to whether execution/evidence failed or oracle is absent | Adapter/tool error and artifact references, if safe. |
| Test assertion fails | `Failed` only against an authoritative configured expectation | Expected/actual and evidence. |
| Timeout | `Failed` only if explicit timeout assertion violated; else `Error` | Configured timeout and observed duration. |
| Retry result differs (failure then pass) | `Flaky`; preserve all attempts | Attempt sequence and per-attempt evidence. |
| Worker crash/restart | Mark interrupted attempt `Error` unless safe evidence supports another explicit status; recover run without false `Passed` | Last persisted state, partial evidence, restart/retry options. |
| User cancellation | Run `Cancelled`; unstarted checks `Skipped`; retain completed/partial evidence | Cancellation point and cleanup result. |
| AI unavailable/invalid/rate-limited | Bounded retries then deterministic fallback/degraded state; if required step cannot continue, `Blocked`/`Error` | Provider/model/task and failure; AI-off usable path remains. |
| Artifact missing/corrupt/redaction failure | Never claim evidence complete; check may be `Error`/`Inconclusive`, run may be partial | Missing artifact ID/hash and impact. |
| Report generation/schema/persistence error | Do not claim normal completion; exact `Partial`/`Failed` selection to be finalized | Which reports/state persisted and retrieval/recovery action. |

## 4. Retry, rerun, and idempotency

- A retry is a new attempt; never overwrite a prior attempt or evidence. Failure followed by pass is `Flaky`.
- `rerun` may rerun selected checks but must preserve earlier attempts and audit history. The exact CLI syntax and selection semantics are TBD.
- Retry count/backoff and whether `Flaky` requires rerun are stakeholder-approved policy; illustrative `retries: 3` in the SRS prompt is not an approved default.
- State-changing operations (create run, approve, cancel, rerun) need defined duplicate-request behavior before implementation. Idempotency key shape and replay semantics are currently open; replays must not create duplicate workers or repeat destructive side effects.
- A rerun/retry revalidates target, policy, adapter version, plan revision, and approvals. Stale approvals do not carry across material scope or plan changes.

## 5. Recovery and resume behavior

- Persist workflow state and completed attempt evidence across process restart.
- On recovery, inspect worker ownership and leases; do not assume a persisted `Running` state means a live worker is healthy.
- Reconcile worker status, artifact hashes, approvals, target policy, and run snapshot before resume.
- Any attempt whose outcome cannot be proven becomes `Error` or an explicit interrupted outcome; never infer `Passed` from absence of a failure record.
- Resume only at a safe checkpoint. Do not replay a non-idempotent write/destructive action without fresh approval and an approved replay rule.
- Record a recovery audit event with prior state, observed worker state, action taken, and preserved artifacts.
- If evidence DB/files disagree or hashes fail, mark evidence incomplete and prevent a positive verdict unsupported by available evidence.

## 6. Cancellation and cleanup contract

Cancellation and timeout must stop the complete process group, detach/disable egress, remove container/network/volume/temporary credential mounts, and record cleanup success/failure. Partial evidence remains subject to redaction and retention. Cleanup failure is a security incident state requiring clear user notice and operational diagnostic; do not mark it as a clean cancellation.

## 7. Open transition decisions

Approve exact criteria for `Partial`; report-generation failure after successful execution; retry count/backoff; run timeout versus check timeout; recovery after machine reboot; duplicate run/approval API behavior; cancellation race at terminal states; cleanup failure severity; and whether partial result can be exported. Document them in ADRs before implementing durable state transitions.

