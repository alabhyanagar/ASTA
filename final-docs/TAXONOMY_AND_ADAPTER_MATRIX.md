# ASTA Testing Taxonomy and Adapter Capability Matrix

**Status:** Product taxonomy baseline; adapter availability is provisional  
**Sources:** [`PRD.md`](PRD.md) §8; [`SRS.md`](SRS.md) §6; [`TAD.md`](TAD.md) §§5, 7  
**Policy:** User selection is multi-select. A taxonomy item is not a support claim unless a verified adapter, prerequisites, risk policy, and report evidence are available.

## 1. Normalization model

Do not force every label into one mutually exclusive tree. Keep these dimensions separate and combine them for each planned check:

| Dimension | Meaning | Examples |
|---|---|---|
| **Test level / strategy** | How much of a system or what lifecycle is being exercised | Unit, component, integration, system, E2E, acceptance/UAT, regression, smoke, sanity, exploratory, release validation |
| **Domain** | Subject matter or quality area | API/service, web/frontend, database/data, security, performance, reliability, mobile, code quality, DevOps/delivery, test-suite quality |
| **Protocol/platform** | Interface or execution environment | REST, GraphQL, SOAP, WebSocket, browser, Android, iOS, database, container/Kubernetes, OS/device/browser |
| **Technique** | How a check is conducted | Existing test execution, schema/contract, static analysis, crawl, active scan, fuzzing, mutation, visual baseline, load, fault injection |
| **Validation intent** | What assertion or goal is tested | Functional behavior, authentication/authorization, accessibility, performance threshold, data integrity, installation/configuration, regression |

Checks may carry multiple tags. Deduplicate only if target, operation, and assertion are equivalent; preserve every relevant taxonomy/domain label and evidence link. Capability IDs must be stable and versioned. The initial ID namespace and alias policy are not approved yet; do not treat examples below as canonical IDs.

## 2. Final product taxonomy (normalized)

### A. Existing project / functional testing

- **Levels:** unit, component, integration, system, end-to-end (E2E), acceptance/user acceptance testing (UAT).
- **Strategies:** regression, smoke, sanity, exploratory, release validation.
- **Lifecycle/operations:** installation, configuration, alpha/beta validation.
- **Scenarios:** business flows and user journeys.
- **Prerequisites:** supported language/runtime/build ecosystem, explicit commands and fixtures; acceptance/business flow needs user criteria or formal oracle.
- **Boundary:** component/integration scenario must declare white-box or black-box before language binding.

### B. API / service testing

- **Protocols:** REST, GraphQL, SOAP, WebSocket.
- **Check types:** schema/contract, authentication, authorization, boundary/error handling, regression, security, performance.
- **Evidence:** request/response, schema/version, target, assertions, redacted headers/body, timings, and adapter/tool version.
- **Prerequisites:** explicit authorized target, API schema or user-defined criteria where relevant, supported protocol adapter. Weak/no oracle → `Inconclusive` for claims without authoritative assertion.

### C. Web / frontend testing

- Crawl/navigation, forms, sessions, user journeys, responsive behavior, accessibility, screenshot/visual comparison, cross-browser, frontend performance, frontend security.
- **Prerequisites:** reachable or startable app, approved URL/host/path, test data, browser adapter and supported browser/runtime.
- Business workflow expectations must be user-provided or formally specified. Visual baseline storage/approval is TBD.

### D. Database / data testing

- Validation, integrity, consistency, schema, stored procedures, triggers, ETL, migrations, backup, recovery, performance.
- **Prerequisites:** disposable database or explicitly authorized target; supplied connection reference; migration/rollback and write operations need exact per-check approval.
- **Later scope:** database tests are not an initial universal capability; no database adapter is yet committed.

### E. Security testing

- Static analysis/SAST, secrets scanning, dependency scanning, vulnerability assessment, API security, DAST, authorized active scanning, fuzzing, penetration checks, compliance-criteria evaluation.
- **Risk:** static checks on a source copy and passive scans may be Safe subject to policy; active scanning/fuzzing/penetration are Active security and require explicit exact-target authorization; destructive actions also require disposable target. “Compliance evaluation” is not certification.

### F. Performance testing

- Load, stress, spike, endurance, scalability, volume, concurrency, capacity, benchmark.
- Require workload definition, rate/user/duration ceilings, exact target and approval. Results include environment and workload; same-host measurements are indicative.
- **M3 candidate:** bounded Locust or equivalent. No final numeric traffic ceilings, thresholds, SLA, or performance target is set.

### G. Reliability / compatibility testing

- Reliability, availability, failover, recovery/disaster recovery, maintainability, OS/device/browser compatibility, localization/internationalization.
- Requires declared supported environment and an adapter able to capture deterministic evidence. Availability/failover checks may require a disposable or explicitly authorized environment.

### H. Mobile testing

- Android, iOS, device, network, notification, battery, permission.
- Requires device/emulator and a verified adapter. Android is Later scope; no iOS/Android device matrix is committed.

### I. Code quality

- Static analysis, quality scan, technical debt indicators, security code scan, lint.
- Static analysis must not execute/import project modules. Coverage/quality measurements are “not measured” if no supported parser/runner exists; never report absent measurement as zero or pass.

### J. DevOps / delivery

- Build, deployment, infrastructure, container, Kubernetes, CI/CD validation.
- Dockerfile/Compose may enable later static container/config checks but does not establish safe runtime configuration. Container/Kubernetes execution checks require separate threat, target, and authorization review.

### K. Test-suite quality

- Coverage, mutation, flaky/repeatability, duplicate detection, assertion/oracle review, suite maintenance.
- “Automated bug creation” means controlled isolated fault injection/mutation, never real defect injection into the target. Exploratory testing is assisted session planning/evidence capture, not a claim of fully autonomous human exploratory testing. Regression is a strategy applied to underlying suites, not an independent protocol.

## 3. Applicability signal registry

| Detected signal | Candidate capability | Prerequisite / limitation |
|---|---|---|
| OpenAPI/Swagger or reachable schema | REST contract/schema, auth, regression | Target authorization and useful oracle; weak/no oracle may yield `Inconclusive`. |
| Reachable/startable web app | Navigation, forms, responsive, accessibility, screenshots, frontend performance | Approved target; business flow criteria; browser adapter available. |
| Existing tests and runnable commands | Existing test suites and coverage | Supported runtime/command; output parser where coverage is claimed. |
| Supported language/manifests | Static analysis, lint, secrets, dependency tools | Adapter/platform support and license verified. |
| Dockerfile/Compose | Later static container/config checks | Does not imply safe runtime configuration. |
| Database URL and migrations | Database checks | Disposable database and explicit authorization. |
| Android package and emulator | Android checks | Device/emulator adapter. |
| Workload profile and explicit approval | Bounded performance run | Rate/users/duration ceilings and target approval. |

Detection is evidence-based; absent evidence remains unknown. Applicability resolution classifies only within user-approved scope. Additional checks remain recommendations until exact approval.

## 4. Adapter capability matrix

**Status key:** `M1 candidate` / `M2 candidate` / `M3 candidate` / `Later` / `Uncommitted`. These phases are the TAD plan; they are not support claims. Every tool version, license, command, OS, and output parser remains subject to verification.

| Adapter family | Taxonomy covered | Planned phase/status | Tool candidates recorded in TAD/SRS | Required safety/evidence gate |
|---|---|---|---|---|
| Existing project test runner | Unit through E2E; regression/smoke/sanity | M1 candidate | Project-native runner; pytest is a candidate ecosystem | Explicit command; compatible runtime; source read-only; preserve test stdout/stderr, exit, versions, assertions and duration. |
| Deterministic/schema generator | API/service contract; schema-based cases | M1/M2 candidate | Schemathesis; pytest/HTTPX | Approved target; schema version; deterministic input generation; reject out-of-scope URLs; preserve request/response evidence. |
| REST/API adapter | REST, schema/contract, auth/authz, boundary/error | M2 candidate | Schemathesis; pytest/HTTPX | Authorization manifest, credential reference, request rate ceilings, redaction and oracle source. |
| Browser/web adapter | Web navigation/forms/journeys/responsive | M2 candidate | Playwright | Isolated browser; approved host/redirects; screenshots/redaction; explicit business-flow oracle. |
| Accessibility adapter | Web accessibility | M2 candidate | axe-core (possibly browser-integrated) | Supported browser; retain rule/tool versions and affected DOM/context; automated scan is not expert accessibility certification. |
| Static/code quality | SAST, lint, quality, technical debt | M1/M2 candidate | Semgrep; Bandit | Static-only mode cannot import/execute project modules; source copy; rule database/version recorded. |
| Secret scanning | Secret exposure | M2 candidate | Gitleaks | Source copy; findings redacted; test fixtures ensure canary secret not leaked to logs/reports. |
| Dependency/security | Dependency inventory/vulnerability | M2 candidate | pip-audit; OSV-Scanner | Lockfile/package provenance; registry policy; database freshness; distinguish advisory finding from proven exploitability. |
| Passive/active web security | DAST, passive scan, authorized active scan/fuzz | M3 candidate | OWASP ZAP | Passive and active modes distinct; active is per-check authorized; target allowlist and traffic ceilings; report exact scan profile/version. |
| Performance/load | Load/stress/spike/endurance/capacity | M3 candidate | Locust or equivalent | Explicit workload, rate/concurrency/duration ceiling, approved target, stop conditions, environment labels. |
| Database/data | Integrity/schema/procedure/ETL/migration/backup | Later | No exact tool committed | Disposable DB or exact authorization; synthetic data; write/destructive approval; test backup/restore without exposing production data. |
| Visual/cross-browser | Visual baselines, responsive, browser compatibility | Later | Playwright may be candidate; not committed for visual comparison | Approved baseline/review; browser versions; pixel/environment variability captured. |
| Fuzz/property/mutation | Fuzz, property, mutation, controlled fault injection | Later | None committed | Bound input/CPU/time; isolated target; mutation outside source by default; no real defect inserted into user project. |
| Container/Kubernetes/CI | Build, deployment, infrastructure, container, Kubernetes, CI/CD | Later | None committed | Separate infrastructure credentials, least privilege, isolated environment and explicit write/change approvals. |
| Mobile/device | Android/iOS/device/network/notification/battery/permission | Later | None committed | Device/emulator support, permission and data boundaries, per-OS verified adapter. |

## 5. Adapter contract (minimum manifest)

Each registered adapter must declare:

| Field | Required meaning |
|---|---|
| `adapter_id` | Stable namespaced ID and contract version. |
| `capabilities` | Canonical capability IDs and taxonomy tags covered. |
| `applicability_signals` | Deterministic project/target facts and evidence required. |
| `support_state` | Supported, partial, or unsupported for the specific OS/runtime/tool version. |
| `risk_class` | Safe, Needs approval, Destructive, Active security, or High traffic as applicable. |
| `prerequisites` | Runtime, schema, test data, permissions, credentials, target conditions. |
| `tool_name`, `tool_version`, `license` | Exact included/invoked external component metadata. |
| `supported_os`, `supported_runtime` | Verified matrix, not guessed compatibility. |
| `command_template` / `input_schema` | Allowlisted executable/arguments and validated typed input; no free-form model shell string. |
| `output_schema` | Validated structured result plus captured raw evidence reference. |
| `evidence_mapping` | How tool output maps to status, finding, assertion, artifact, and provenance. |
| `limits` | Timeout, CPU, memory, processes, disk/output, network/rate constraints. |
| `unsupported_conditions` | Explicit reasons adapter must return `Unsupported` or `Blocked`. |

An adapter does not assign the authoritative run verdict. Adapter outputs are evidence consumed by the deterministic evaluator.

## 6. Language/framework boundary matrix

| Check mode | Language rule | Status / examples |
|---|---|---|
| White-box unit test | Must use the target module source language and a compatible runtime/build ecosystem unless a verified adapter declares supported binding. | Binding rule is confirmed. Initial language/framework list remains open; Python web/API and plain websites are only a proposal. |
| Black-box API / E2E / UI / performance | May use another supported test language against an isolated running target. | Requires an available verified adapter and an authorized isolated target. |
| Component/integration | Must declare `white-box` or `black-box` before language binding. | Ambiguous scenario cannot advance. |
| Any unsupported or ambiguous language/runtime | Do not silently substitute. | Return `Unsupported` or `Blocked` with reason and prerequisite. |

## 7. Release support claim checklist

Before labeling an adapter supported, record a stable manifest, exact tool/dependency versions, license review, supported OS/runtime, positive and negative applicability fixtures, output schema validation, target/risk enforcement, evidence mapping, resource limits, cleanup behavior, known limitations, and release acceptance evidence. Publish only verified combinations. “Partial” support must state what is not covered.

