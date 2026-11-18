# ASTA Risks, Assumptions, and Open Decisions Register

**Status:** Initial register; assign accountable owners and target dates before implementation planning  
**Sources:** [`PRD.md`](PRD.md) §§4, 11; [`SRS.md`](SRS.md) §§12–13; [`TAD.md`](TAD.md) §§16–17  
**Related:** [`ADR_REGISTER.md`](ADR_REGISTER.md), [`SECURITY_THREAT_MODEL.md`](SECURITY_THREAT_MODEL.md)

## 1. Register conventions

- **Risk:** uncertain event with impact; needs mitigation and evidence.
- **Assumption:** planning premise, not a confirmed fact; validate before dependent work.
- **Open decision:** stakeholder choice, experiment, or policy still required.
- No owner/date is invented here. Assign both during project kickoff.
- Severity and likelihood scores are intentionally blank until the team adopts a scale.

## 2. Risks

| ID | Risk | Impact | Mitigation / evidence gate | Affected release | Owner / status |
|---|---|---|---|---|---|
| R-01 | Docker or chosen container boundary fails to contain malicious project code | Host compromise or credential/data loss | Trusted-only projects or read-only analysis until platform-specific containment/effectiveness test passes; assess rootless/VM options. | M1 execution | TBD / Open |
| R-02 | Egress control can be bypassed through redirects, DNS/IP/IPv6 variation, metadata, or local routes | Unauthorized target access/SSRF | Deny by default; per-request policy; direct-IP, redirect, IPv6, DNS, localhost/private/metadata proof. | M1 | TBD / Open |
| R-03 | Project or package install hooks execute outside intended boundary | Host compromise, supply-chain exposure | Isolate installation; approved registries; source read-only; resource controls; record dependency provenance. | M1 | TBD / Open |
| R-04 | Project has insufficient authoritative test oracles | False pass/fail and misleading user confidence | Explicit expectation provenance; AI-only expectation → `Inconclusive`; expose gaps and limitations. | M1 | TBD / Open |
| R-05 | Generated tests are syntactically valid but lack meaningful assertions | Low-value or false-positive tests | Deterministic/schema-first generation; require assertion validation; review plan; benchmark planted defects and false positives. | M1/M2 | TBD / Open |
| R-06 | AI output or prompt injection alters intent or is mistaken for evidence | Unauthorized actions or unreliable verdict | One bounded schema-validated gateway; no policy tools; evaluator isolated; AI-off path; injection fixtures. | M2 | TBD / Open |
| R-07 | Local model exceeds expected memory/latency or has incompatible license | Poor UX, unsupported hardware, redistribution constraints | Benchmark latency/memory/quality and review model license before selecting; keep gateway optional. | M2 | TBD / Open |
| R-08 | Secrets appear in reports, artifacts, prompts, or logs | Credential compromise and privacy incident | Minimize collection, scoped references, redaction canaries, remote-content preview, retention/deletion controls. | M1 | TBD / Open |
| R-09 | Performance/security checks harm production target | Service degradation or data damage | Safe-only proposed default; per-check target approval; rate/duration limits; disposable data; stop conditions. | M2/M3 | TBD / Open |
| R-10 | Tool/version/license or OS incompatibility invalidates support claims | Legal/release risk or unreliable execution | Adapter manifest, exact-version matrix, license review, positive/negative fixtures per release. | All | TBD / Open |
| R-11 | Run state and artifact files diverge after crash or deletion | False replay/result or lost evidence | Hash references, restart reconciliation, explicit incomplete state, consistent backup/restore design. | M1 | TBD / Open |
| R-12 | Benchmark answer leaks into agent/worker context | Inflated accuracy and misleading product quality | Keep answer key outside agent and worker; independent scoring after run. | M1 | TBD / Open |
| R-13 | Multi-domain findings duplicate or conflict | Confusing report and inaccurate overall result | Deduplicate only equivalent target+operation+assertion; preserve all tags/evidence; run comparison fixtures. | M1/M3 | TBD / Open |
| R-14 | User interprets tested-scope pass as whole-project safety/certification | Business or compliance reliance beyond evidence | Report exact scope/counts/gaps/limitations; never claim bug-free/security/compliance/release-ready. | All | TBD / Open |
| R-15 | Platform support is too broad for first release | Delayed delivery and hard-to-reproduce failures | Select narrow OS/language/runtime matrix; publish verified support only. | M1 | TBD / Open |

## 3. Assumptions (unvalidated)

| ID | Assumption | Evidence needed / decision trigger | Status |
|---|---|---|---|
| A-01 | Initial release is single-user and local-first, one worker per machine | Confirm product deployment boundaries and concurrent CLI/MCP behavior. | Product direction confirmed; operational specifics open. |
| A-02 | A CLI is the first dependable interface; MCP shares the core | Verify target MCP hosts support required user confirmation; retain CLI fallback. | Confirmed direction; exact MCP operations/schemas open. |
| A-03 | SQLite and local content-addressed files can serve initial single-machine use | Measure transaction/concurrency needs; decide backup/deletion and crash consistency. | Proposed only. |
| A-04 | Python can serve the control plane and first adapters | Define tested project languages separately; test packaging/OS. | Recommended only. |
| A-05 | Initial project samples can be limited (proposal: Python web/API and plain websites) | Product owner approves actual language/framework support matrix. | Not approved. |
| A-06 | Local Ollama is a reasonable first optional AI provider | Benchmark supported hardware/model quality, latency, license, and UX. | Proposed only. |
| A-07 | Safe-class checks can be a production default | Stakeholders approve risk policy and supported environments. | Proposed; final production policy TBD. |
| A-08 | User can provide authorization manifests and test data for reachable targets | Validate user workflow and target ownership evidence. | Needs product/legal review. |
| A-09 | Generated artifacts outside source tree meet initial workflow needs | Validate how users inspect, version, rerun, and export artifacts. | Baseline direction; user experience details open. |

## 4. Open decisions before M1 coding

| ID | Decision | Options/known state | Blocking consequence |
|---|---|---|---|
| D-01 | OS, hardware, and sandbox runtime | Prove Windows+WSL2/Docker or select Linux; Docker proposed, not a hostile-code guarantee. | Cannot claim supported untrusted execution until proof. |
| D-02 | Initial project languages/frameworks | Python web/API and plain websites proposed; none finalized. | Determines M1 adapter, CI fixture, packaging, and support claims. |
| D-03 | Product/package/CLI command name | `testagent` appears illustratively only. | Package, executable, docs, installation contract. |
| D-04 | Archive limits | File count, compressed size, expanded size, expansion ratio all TBD. | Archive intake cannot be safely accepted without limits. |
| D-05 | Sandbox fallback policy | Trusted-only duration versus stronger isolation; read-only mode is available direction. | Execution eligibility and user-facing status. |
| D-06 | Safe and risk approval policy | Safe-only production default proposed; approval authority and evidence format TBD. | Which checks may run and how approval is collected. |
| D-07 | Severity scale | Critical/High/Medium/Low/Informational are candidate labels. | Finding/report schema and triage. |
| D-08 | Retry/flaky policy | Retry count/backoff and rerun policy user-approved; illustrative `retries: 3` is not approved. | Attempt classification and runtime bounds. |
| D-09 | Quality thresholds | Coverage, mutation, defect recall, false-positive target, benchmark minimum TBD; proposed 50% planted API defect recall is explicitly unapproved. | Cannot claim benchmark quality or suite acceptance. |
| D-10 | AI model/provider | Local Ollama proposed first; exact model, hardware, license, remote service policy TBD. | M2 capability selection and privacy disclosure. |
| D-11 | Data retention/encryption/backups | Durations, secret store/encryption, deletion and backup semantics TBD. | Persistence implementation and privacy commitments. |
| D-12 | External tool licenses and versions | All candidate tools need exact-version and license review. | Cannot bundle, distribute, or advertise integrations. |
| D-13 | API authentication and multi-user | Local token proposal; lifecycle/network binding/roles TBD; multi-user is Later. | M3 API security contract. |
| D-14 | Performance ceilings and service targets | Rate/users/duration, latency, concurrency, availability/SLA TBD. | Cannot safely run load tests or make production performance claims. |
| D-15 | Remote AI opt-in UX and disclosure | Preview selected content, explicit opt-in, audit requirement; exact UX/data categories TBD. | Remote AI must remain off until approved. |
| D-16 | Fix mode and CI timing | Both Later; fix disabled by default, separate copy/branch and explicit authorization. | Do not implement in M1/M2 without scope change. |
| D-17 | REST/API and UI implementation | FastAPI+Pydantic and React+TypeScript+Vite are M3 candidates. | Preserve as candidates until M3 acceptance/auth design. |
| D-18 | Schema, IDs, and versioning | Report schema_version required; exact JSON/YAML/API schemas, identifier format, migration policy TBD. | Block storage/API implementation until contracts approved. |
| D-19 | Package delivery shape | Locally installed app confirmed; `.exe`/installer/package undecided. | Must settle before distribution/installer work and support claim. |

## 5. Immediate decisions and evidence sequence

1. Assign an accountable owner and target date to each `D-*` item; decide the M1-blocking items first: D-01 through D-06, D-11, D-18, and D-19.
2. Select one narrow source language/framework and one OS/runtime fixture before defining M1 adapter support.
3. Prototype/validate the worker and egress security boundary before enabling untrusted code execution.
4. Approve capability IDs, config/report schemas, status transition guards, and immutable approval binding before persisting runs.
5. Approve numeric resource, archive, retry, performance, and benchmark limits before release acceptance.
6. Review candidate tool/model licenses and privacy implications before bundling or remote transmission.

## 6. Review cadence

Review this register at each milestone exit and whenever a threat-model control, support claim, data-retention promise, or user-approval workflow changes. Close an item only when a named decision/evidence link is recorded in the ADR or baseline document. Preserve superseded entries for traceability.

