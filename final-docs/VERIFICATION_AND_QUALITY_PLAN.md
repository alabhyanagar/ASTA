# ASTA Verification and Quality Plan

**Status:** Planned verification contract; no implementation tests have been run  
**Sources:** [`SRS.md`](SRS.md) §§8, 10–14; [`PRD.md`](PRD.md) §10; [`TAD.md`](TAD.md) §§10, 15

## 1. Objective

Verify that ASTA performs only approved checks, preserves evidence and provenance, reports truthful results, and behaves predictably when prerequisites, adapters, AI, workers, or storage fail. Test quality is measured by relevant evidence and safety properties, not by a coverage percentage alone.

This is a plan for future product verification; it does not claim the software exists or that the described checks have been executed.

## 2. Verification methods

- **Test:** execute a component/system against defined expected behavior.
- **Inspection:** review configuration, manifests, reports, source boundaries, licenses, or deployment artifacts.
- **Analysis:** evaluate benchmark measurements, risk, resource use, or evidence consistency.
- **Demonstration:** walk through representative user workflows and observe outputs.

Every release claim must cite evidence location, build/tool version, environment, requirement IDs, observed outcome, and known limitation.

## 3. Quality gates (must pass in order)

### Gate A — Requirements and design readiness

- SRS IDs have acceptance methods and owners in [`TRACEABILITY_MATRIX.md`](TRACEABILITY_MATRIX.md).
- Initial OS/project-language/adapter scope, thresholds that block release, and policy defaults are approved.
- Security threat model reviewed; trust boundaries and fail-closed behavior agreed.
- Data/report schemas and migration/deletion/retention rules versioned before implementation.
- No unresolved decision allows ambiguous authority or automatic execution of recommendations.

### Gate B — Component contract readiness

- Config schema rejects invalid fields before side effects; config cannot broaden runtime safety policy.
- Adapter manifest, capability states, input/output schemas, tool/license metadata, and resource ceilings validate.
- Evaluator golden results are deterministic and do not import/call AI.
- Approval freshness, content hash, immutable run snapshot, and report `schema_version` contracts are tested.

### Gate C — Safe execution proof

- Missing approval, sandbox, adapter, prerequisite, or target authorization results in no worker start or a clear read-only mode.
- Worker source mount is read-only and output is separate; process, CPU, memory, disk, output, and wall-clock ceilings are enforced.
- Network default is deny; only approved target is reachable; local, metadata, redirect, DNS, IP, and IPv6 escape paths are blocked.
- Package installation is separated and limited to approved registries; test execution is offline except approved target.
- Cancellation/timeout/crash cleanup removes worker group, network, volumes, and credential access; partial evidence is retained.
- Archive, output, report HTML, and artifact path attacks are contained.
- Canary secret absent from database, logs, model prompt/reply where disallowed, screenshots, traces, reports, and artifact metadata.

### Gate D — Release acceptance

- Full supported CLI journey: add project → inspect → plan → review/approve → run → evaluate → domain reports + consolidated report.
- Replay a planted-defect “bug garden” run from stored plan/scripts/tool versions/evidence without another model call.
- All attempt statuses and run verdict branches have golden cases.
- AI-off supported workflow completes; provider unavailable/invalid output degrades safely.
- Benchmark reports recall, false positives, duplicates, flaky outcomes, coverage gaps, and runtime. Thresholds are approved before using benchmark to claim quality.
- Publish exact supported OS/project-type/tool matrix and limitations; complete license, privacy, security, and retention evidence before corresponding claims.

## 4. Verification matrix

| Test area | Representative cases | Required result/evidence |
|---|---|---|
| Intake | Local folder, archive, public repository, authorized URL; unsupported input; hostile archive | Provenance captured; unsupported reason explicit; traversal/symlink/device/expansion attacks cannot escape workspace. |
| Scope resolver | Single and multiple selected types; aliases; conflicting config; unrequested recommendation; changed scope | Every requested type canonicalized; no silent additions; runtime policy remains hard ceiling; approval invalidated by material change. |
| Capability registry | Positive, negative, unknown and partially supported project signals | State/reason and evidence returned; unknown remains unknown; no false support claim. |
| Planner/approval | User edit, exclusion, recommendation approval/decline, plan hash/revision change, high-risk check | Exact approval required; stale approval rejected; declined/pending check never executes. |
| Language boundary | White-box unit in matching and mismatching language; black-box cross-language; ambiguous integration | Mismatch blocked unless binding declared; black-box requires supported adapter/isolated target; ambiguous classification cannot advance. |
| Adapter | Valid/invalid config/output, missing tool, unsupported OS, no assertion, duplicate checks | Output schema enforced; `Unsupported`/`Blocked` explained; equivalent target+operation+assertion deduplicated with tags preserved. |
| Execution | Runaway process, resource exhaustion, source write, no network, approved target, denied host, dependency install | Source remains unchanged; ceilings enforce; target policy obeyed; phase-specific network behavior recorded. |
| Egress/SSRF | Domain, direct IPv4/IPv6, DNS change/rebinding, redirects, localhost/private/link-local/metadata | Authorized target only reachable; every denial logged; redirect/address policy rechecked. |
| Evaluator | Each status, authoritative versus AI-only expectation, retry fail→pass, timeout, no measured coverage, each overall verdict branch | Identical inputs yield identical results; AI-only assertion is `Inconclusive`; timeout rule exact; gaps never become zero/pass. |
| AI gateway | Offline, malformed schema, refusal, rate limit, timeout, prompt injection, remote opt-in/out | Bounded retries then fallback/degraded/Blocked/Error; AI-off works; no policy, scope, approval, evidence, or verdict mutation; remote choice audited. |
| Reports | Multi-domain, every disposition, redaction, missing artifact, JSON schema, HTML injection | One report per selected domain plus one consolidated; counts reconcile; safe rendering; `schema_version`; missing evidence explained. |
| Reliability | Cancel queued/active, worker crash, app restart, report failure, partial evidence | No false `Passed`; attempts/audit preserved; explicit cancellation/error/partial state; cleanup outcome recorded. |
| Compatibility | Supported OS/runtime/tool version and unsupported combination | Published matrix matches verified cases; no implicit fallback to a different language/tool. |

## 5. Evaluator golden contract

Golden fixtures must cover:

1. Each attempt status: `Passed`, `Failed`, `Flaky`, `Skipped`, `Blocked`, `Inconclusive`, `Unsupported`, `Error`.
2. Each authoritative expectation source: user criteria, formal specification, existing test, configured threshold, defined universal check.
3. AI-only expectation results in `Inconclusive`, never a pass/fail.
4. Retry sequence fail then pass is `Flaky`; all attempts remain stored.
5. Timeout is `Failed` only when explicit configured timeout assertion is violated; otherwise `Error`.
6. Run verdict: any Failed → `Failures found`; no Failed plus any Flaky/Error → `Unreliable results`; at least one Passed and no Failed/Flaky/Error → `Passed in tested scope`; otherwise `No result`.
7. Quality disposition remains separate: `Accepted`, `Needs review`, `Rejected`.
8. Unmeasured coverage/mutation is `not measured`, not zero/pass.

## 6. Bug-garden/benchmark plan

Maintain representative supported sample projects and controlled defects. Keep benchmark answer keys outside the agent/worker context. Record project revision, expected defect/capability, adapter/tool version, run plan, attempts, evidence, report, and environment. Report precision/recall or recall, false positives, duplicate rate, flaky outcomes, coverage gaps, and runtime as applicable. No numeric threshold (including the proposed 50% planted API defect recall) is approved until stakeholder review.

## 7. Performance, reliability, and usability measurements

- Measure inspection, planning, queue, execution, evaluation, report composition, and artifact I/O separately.
- Capture CPU, memory, process, disk, output, wall-clock, target rate/users/duration, model latency/resource use, and concurrency.
- Performance reports disclose workload, environment, ceilings, and same-host comparability limits.
- Numeric service targets (latency, throughput, availability/SLA, maximum project/archive size, concurrency) are TBD and must be approved before production acceptance.
- Walk through CLI approval, config errors, blocked/unsupported states, cancellation, report reading, and AI-off usage. M3 UI additionally checks keyboard access, semantic labels, and readable status indicators.

## 8. Release evidence package

Each release includes: traceability closure export; supported OS/project/tool matrix; threat-model proof results; benchmark summary; evaluator goldens; adapter validation records; licensing inventory; schema/report version; known issues and `Blocked`/`Unsupported` limitations; installation/recovery steps; and approved residual risks. Store raw evidence and derived summaries separately and retain according to approved policy.

