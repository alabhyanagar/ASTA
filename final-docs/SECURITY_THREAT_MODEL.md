# ASTA Security and Privacy Threat Model

**Status:** Design baseline; proof pending  
**Scope:** Local-first ASTA application, its interfaces, adapters, AI gateway, worker, and report/artifact path  
**Related:** [`SRS.md`](SRS.md) §§4–9, 11–13; [`TAD.md`](TAD.md) §§3–9, 14, 16; [`VERIFICATION_AND_QUALITY_PLAN.md`](VERIFICATION_AND_QUALITY_PLAN.md)

## 1. Security objective

ASTA must help an authorized user test a project without letting untrusted project content, test scripts, dependencies, model output, or tool output silently broaden scope, escape the execution boundary, expose secrets, corrupt the host, or fabricate a trustworthy result. It must fail closed when required authorization or isolation is unavailable.

This design does not claim ASTA is a penetration-testing certification product or that a container alone makes deliberately malicious code safe.

## 2. Assets and security properties

| Asset | Required property |
|---|---|
| Host machine and user files | Project execution cannot read/write host paths beyond the approved source read mount and separate run output. Host home, Docker socket, and unrelated workspaces are not mounted. |
| Project source and revision | Source provenance is recorded; source is read-only during ordinary checks; source changes are detectable by hash; archive extraction cannot escape workspace. |
| Target systems and data | Only exact authorized targets/actions are reachable; active/destructive/high-traffic operations are separately authorized and bounded. |
| Credentials and tokens | Secret values stay outside ordinary project/plan/run/report records; workers receive narrow, short-lived references; logs and artifacts redact recognized secrets. |
| Scope, plan, and approvals | Approval binds to exact plan/scope revision and content; a changed plan or target invalidates impacted approval. |
| Findings, evidence, and verdicts | Evidence is attributable and replayable; evaluation is deterministic; AI cannot authoritatively set pass/fail. |
| Model prompts/replies | Remote disclosure is explicit and minimized; content is treated as untrusted; outputs are schema-validated and cannot call arbitrary tools. |
| Audit records | Approval, target, AI sharing, egress, cancellation, and artifact access decisions are recorded with run/component identity. |
| Artifacts/reports | Paths and content are validated, secrets redacted, HTML escaped, and access checked when exposed through API/UI. |

## 3. Actors and trust assumptions

- **Project owner/tester:** chooses source, target, test types, and approvals. Product assumes this user may make mistakes; risky operations require clear exact-scope confirmation.
- **Project author/source:** source files, archives, manifests, tests, documentation, and startup hooks may be malicious or misleading.
- **Dependency/tool supplier:** package registries, build tools, testing tools, and adapters can be compromised or behave unexpectedly.
- **Target operator:** may own the target or may not; ASTA must not infer authorization from URL reachability.
- **AI provider/model:** can be unavailable, inaccurate, adversarially influenced by content, or return malformed output. Model output is not trusted policy or evidence.
- **External network/target:** may redirect, resolve to different addresses, return hostile content, or contain sensitive data.
- **Local same-user process:** can potentially access local files depending on OS permissions. The initial single-user local design does not claim isolation from a fully compromised user account.

## 4. Trust boundaries

```text
User / CLI / MCP host / later API or UI
             │ validated request; no interface grants policy
             ▼
Trusted control plane: intake → scope/risk → planner → approval → coordinator
             │ immutable run snapshot; narrow worker capability references
             ▼
Execution boundary: sandbox controller → isolated worker → project/tool code
             │ only approved target through egress controller; bounded artifacts
             ▼
Evidence validation/redaction → deterministic evaluator → report composer
             │ versioned records; secret-safe content
             ▼
Local database + content-addressed artifact store + OS/encrypted secret store

Optional AI gateway: receives bounded, disclosed inputs; returns schema-validated
advisory data only. It has no authority over target, approval, verdict, or evidence.
```

The control plane, worker, persistence, egress proxy, secret store, and optional model service are separate logical trust zones. Exact process/container topology remains contingent on the chosen OS and sandbox proof.

## 5. Threat scenarios and required controls

| ID | Threat / example | Required control | Proof before supported execution claim |
|---|---|---|---|
| TM-01 | Archive path traversal, unsafe symlink, device file, decompression bomb | Validate archive paths/types before extraction; enforce file-count, compressed/uncompressed size and expansion ceilings; extract only into a fresh run workspace. Caps are TBD and must be set before release. | Malicious archive fixtures prove no write outside workspace and fail with field-specific reason. |
| TM-02 | Project test reads host secrets or mutates source | Worker has least privilege, source read-only, separate output, no host home or Docker socket, minimal environment, CPU/memory/process/disk/output/time limits. | Source tree hash unchanged; host canary paths unavailable; resource exhaustion terminates worker. |
| TM-03 | Worker reaches unauthorized service via direct IP, DNS rebinding, redirect, IPv6, localhost, or cloud metadata | Network deny by default; controller validates each request/redirect and resolved address; allowlist exact target scope; block local/link-local/metadata ranges unless explicitly authorized; dependency installation has a separate approved registry policy. | Tests cover DNS, IPv4/IPv6 literals, redirect chains, alternate encodings, loopback, private ranges, metadata addresses, and allowed/denied hosts. |
| TM-04 | SSRF or scope expansion from user/project/API specification | Canonicalize and bind target, URL/path, environment, action; check before plan approval, before execution, and on every worker request. API specs and discovered routes are input data, not authority. | Out-of-scope target/redirect and changed-manifest fixtures are blocked and audited. |
| TM-05 | Active, destructive, or high-traffic checks harm live systems | Risk classify each check; safe-only proposed default; exact per-check approval, target in manifest, disposable data/target where required, and configured traffic/destructive ceilings. | Missing approval blocks; traffic stops at ceiling; destructive fixture only reaches disposable test target. |
| TM-06 | Prompt injection in repository docs, pages, tests, or tool output persuades AI to alter scope/run commands | Treat all project/target/tool content as untrusted data; no model tools that can authorize/execute; bounded task input and output schema; deterministic policy and scope controls outside AI. | Prompt-injection fixture cannot change plan scope, invoke tool, approve a check, alter evaluator policy, or change a verdict. |
| TM-07 | AI hallucination is presented as confirmed finding or pass/fail | Label confirmed/inferred, cite existing evidence IDs, reject invalid references; AI-only oracle → `Inconclusive`; evaluator isolated from AI. | Evidence-reference validation and import-boundary checks; AI-only expectation golden case. |
| TM-08 | Secret appears in logs, prompt, screenshot, report, database, or crash dump | Secret references only; short-lived scoped injection; redact before persistence/export/model input; avoid credential-field screenshots; retention/deletion policy. | Canary-secret test across stdout/stderr, logs, prompts/replies, screenshots, traces, JSON/HTML reports, DB, and artifact metadata. |
| TM-09 | Package installation runs malicious hooks or fetches arbitrary content | Separate installation from execution; allow only approved package registries; capture lockfile and tool/package versions; install in disposable worker; default execution network off. | Install and execution phases show distinct network policy; unapproved registry blocked; resulting environment provenance captured. |
| TM-10 | Generated or adapter script executes arbitrary shell or escapes intended target | Use registered adapter commands and schema-validated parameters; scripts derived from approved plan; parse/validate, require meaningful assertion, reject out-of-scope target; no arbitrary LLM shell string. | Invalid, assertion-free, malformed, path-escape, and out-of-scope scripts are rejected before worker starts. |
| TM-11 | Approval replay or time-of-check/time-of-use target drift | Approval binds exact run/scope/plan revision/content hash and policy version; recheck target/manifest before each network action; material change invalidates approval. | Change target/plan after approval; old approval rejected and audit explains why. |
| TM-12 | Worker crash/cancel leaves containers, network, credentials, or child processes | Track worker/process group/resources; cancellation/timeout kills group; cleanup in every exit path; preserve partial evidence and cleanup outcome. | Success, failure, timeout, crash, and cancellation fixtures leave no active worker/network/credential mount. |
| TM-13 | Artifact path traversal, malicious HTML, oversized output, or evidence substitution | Content-addressed artifact references; safe path resolution; output caps; content type validation; HTML escaping; hash and provenance stored; access checks for future API downloads. | Traversal/XSS/oversize/tamper fixtures rejected or safely rendered; hash mismatch detected. |
| TM-14 | Finding/report implies global safety or hides unsupported tests | Report declared scope, environment, all status counts, gaps, evidence, limitations, and “not measured” values; no legal/security/release certification claims. | Report fixtures verify limitations and counts; unmeasured coverage never appears as zero or pass. |
| TM-15 | Third-party adapter/tool/license compromise or unsupported platform behavior | Adapter registry records stable ID, tool/version/license, supported OS/runtime, risk, prerequisites, command schema, evidence mapping; review before enabling/distribution. | Reproducible adapter manifest; license and platform evidence attached to release support matrix. |
| TM-16 | Local DB/file corruption or tampering creates false replay/verdict | Transactional state updates, content hashes, immutable attempt/evidence history, consistency checks; backup/recovery rules must be decided. | Corrupt/missing file produces explicit `Error`/incomplete evidence, never `Passed`; restore drill before claiming backup support. |

## 6. Secret, privacy, and retention rules

1. Credential values do not belong in `Project`, `Target`, `TestPlan`, `Run`, `Finding`, or `Report` records. Store only a `CredentialReference` and purpose/target restrictions.
2. Pass only the minimum scoped secret to the worker and only for the approved check. Do not forward the full host environment.
3. Redact recognized secrets before any logs, artifacts, model inputs, reports, or persistence are written. Because redaction cannot identify every secret, minimize collection first.
4. Remote AI is disabled unless the user explicitly opts in. Disclose and preview selected content; record provider, model, task, data-sharing decision, and outcome.
5. Enforce configurable retention/deletion for source snapshots, prompts/replies, scripts, logs, evidence, and reports. Retention durations, encryption choice, and backup behavior remain TBD.
6. Deletion must account for DB rows, files, prompts/replies, scripts, derived reports, temporary workspaces, and backups under the eventual policy.

## 7. Fail-closed conditions

Block execution (or permit only explicitly configured read-only analysis) when any of these holds:

- Required scope/authorization or exact plan approval is absent, declined, stale, or mismatched.
- Target cannot be canonicalized or an address/redirect cannot be proven in scope.
- Required adapter, runtime, prerequisite, test data, or resource ceiling is unavailable/unknown.
- Isolation boundary or required egress enforcement is unavailable.
- Script/adapter arguments or output fail validation.
- A required secret is unavailable or its approved target/action does not match.
- Worker cleanup, policy version, or audit prerequisite cannot be established.

The user-facing outcome must identify `Blocked`, `Unsupported`, `Awaiting authorization`, or `Error` as appropriate and explain the reason. Do not turn these into a successful empty run.

## 8. Security proof gate

Before allowing untrusted projects to execute, demonstrate on every claimed OS/runtime: read-only source; no host path/socket access; resource ceilings; worker/process termination; DNS/IP/IPv6/redirect/metadata controls; dependency install separation; scoped credential handling; artifact/output limits; and cleanup on every exit. Until then, use trusted projects only or read-only analysis as the TAD states.

## 9. Unresolved security decisions

Operating system and sandbox runtime; Windows+WSL2/Docker versus Linux; trusted-only period; private-target policy; archive caps; exact egress implementation; secret store/encryption; data retention and backups; provider endpoint allowlist; authorization evidence format; target environment policy; and whether/when active security or performance checks may be enabled in production. Track these in [`RISKS_ASSUMPTIONS_OPEN_DECISIONS.md`](RISKS_ASSUMPTIONS_OPEN_DECISIONS.md) and ADRs.

