# Product Requirements Document: Autonomous Software Testing Agent

**Status:** Product and architecture baseline for review  
**Version:** 1.0  
**Date:** 2026-11-18  
**Implementation status:** Not started; this document authorizes planning only, not coding.

## 1. Executive summary

The Autonomous Software Testing Agent (ASTA) analyzes an existing application repository, helps a user select testing scope, prepares a language-neutral test plan, generates tests using compatible language/framework adapters, executes them in isolated environments, assesses test quality, and produces evidence-backed reports. It can propose additional test types, but it must obtain explicit user approval before adding them to the execution scope. Users may select multiple testing types. Every selected domain receives an individual report and the run also produces one consolidated report.

The system is an auditable, user-directed testing workflow—not an unrestricted code-writing agent. It uses deterministic analysis and test tools wherever practical, with AI assisting in scenario synthesis, code generation, diagnosis, and repair proposals. Plans, generated changes, commands, test outcomes, and repair attempts remain reviewable.

## 2. Product decisions (final)

| Decision | Final rule |
|---|---|
| Test selection | Multi-select domains and individual types; users can combine them in one run. |
| Additional recommendations | The agent may recommend tests beyond the selected scope. It must explain the rationale and prerequisites, then wait for explicit user approval before executing any newly recommended type. |
| Reporting | Produce a report per selected testing domain and a consolidated run report linking all domain reports and shared evidence. |
| Planning approval | Present a structured, editable test plan and require approval before generation/execution, subject to an explicitly configured non-interactive policy. |
| Source-code changes | Generated tests and repair patches are reviewable; the agent does not silently change application behavior. Approval is required for assertion changes and other sensitive repairs. |
| No coding now | This PRD and the companion TAD are design deliverables only. |

## 3. Vision, goals, and non-goals

### Vision

Give developers and QA teams one controlled workflow to select, plan, generate, execute, and evaluate meaningful tests across application layers and technology stacks.

### Goals

1. Make the requested test scope explicit, structured, and user-controlled.
2. Turn repository evidence into traceable test scenarios before writing test code.
3. Support multiple testing layers through pluggable adapters and a common execution contract.
4. Isolate untrusted source, generated tests, dependencies, and test data during execution.
5. Evaluate value and reliability, not just whether generated tests pass.
6. Provide actionable evidence through domain reports and a unified report.
7. Support incremental, change-aware runs while retaining a full-suite option.

### Non-goals for the initial product

- Claiming that a passing run proves an application is correct or secure.
- Executing arbitrary generated scripts on the host or against production systems.
- Autonomously modifying application business logic or weakening assertions to make tests pass.
- Supporting every language, framework, mobile device, CI provider, or scanner in the first release.
- Replacing a dedicated penetration test, compliance audit, usability study, or performance lab.
- Automatically opening or publishing defect tickets without an explicit user-configured integration policy.

## 4. Users and primary jobs

| Persona | Job to be done |
|---|---|
| Application developer | Select unit/component tests for changed code; inspect proposed cases and patches; receive fast, actionable feedback. |
| QA engineer | Combine API, integration, E2E, regression, exploratory support, and acceptance checks; track scenario outcomes. |
| Security engineer | Select approved source, dependency, API, and dynamic security checks within an authorized target boundary. |
| Performance engineer | Generate bounded workload scenarios and compare latency, throughput, and error rates in an approved environment. |
| Release engineer | Run smoke, sanity, compatibility, deployment, and release validation with clear go/no-go evidence. |
| Engineering lead | Review consolidated quality, coverage, risk, and unresolved limitations across domains. |

## 5. Product principles

- **Scope belongs to the user.** A recommendation is not authorization.
- **Evidence over confidence.** Report what was inspected and executed, with limitations.
- **Plan before code.** The test scenario and expected behavior should be reviewable first.
- **One canonical concept, many views.** Duplicated labels in the source diagrams map to one canonical test type with domain tags.
- **Adapters isolate ecosystem differences.** Planning and reporting contracts remain language-neutral.
- **Safe defaults.** No production targeting, host secrets, unrestricted network, or unbounded retries.
- **Reviewable autonomy.** Repairs are small, bounded, attributable patches with an audit trail.

## 6. Product workflow

1. **Import project:** local directory or Git checkout; identify repository root and user-supplied target/environment configuration.
2. **Analyze:** detect languages, frameworks, manifests, test suites, API descriptions/routes, database schemas, CI configuration, and change set when available.
3. **Select scope:** user chooses multiple domains/types through CLI, configuration, or natural language. Show detected prerequisites and support status.
4. **Resolve scope:** validate each selection as supported, partially supported, or unsupported. Never silently drop a choice.
5. **Recommend:** optionally suggest additional types with rationale, cost/risk, target requirements, and expected evidence. Recommendations remain pending until approved.
6. **Plan:** create language-neutral scenarios with stable IDs, targets, preconditions, data needs, priority, and expected assertions.
7. **Review and approve:** user edits/approves the plan and any additions to scope. The plan records the approval state and revision.
8. **Generate:** create tests using selected compatible adapters; write to a reviewable workspace/patch area.
9. **Execute:** run only approved scope in isolated environments under policy limits.
10. **Evaluate:** parse outcomes, coverage, mutation, repeatability, quality checks, and artifacts; classify failures.
11. **Repair (bounded):** propose narrow fixes to generated tests/fixtures/environment; rerun within configured retry cap. Ask for human approval for assertion modifications, skips, or ambiguous expected behavior.
12. **Report:** emit per-domain reports and a consolidated report; preserve evidence and traceability.

### Scope validation states

- **Supported:** prerequisites detected and adapter/environment available.
- **Partially supported:** some techniques can run; missing capabilities are stated.
- **Unsupported:** required target or adapter is absent. Do not substitute a different test type without approval.

## 7. Selection flows

All three interfaces must resolve to the same versioned, validated scope model.

### CLI

Illustrative interface, not an implementation commitment:

```text
testagent run --types unit,integration,api,regression
testagent run --types security,performance --profile release-readiness
testagent plan --request "Test payment and authentication with API and integration tests"
```

CLI behavior: accept repeated/comma-separated selections; support include/exclude and per-type options; print resolved scope and unsupported selections; in interactive mode ask for approvals; in non-interactive mode stop safely if required approvals are missing. A `--yes`-style flag must never override policy-defined approvals for expanded scope or sensitive changes.

### Project configuration

`.testagent.yaml` expresses defaults and run policy. CLI values override project defaults, and explicit user run instructions override defaults only for that run. Conflicts are shown in the resolved plan. Configuration is declarative and schema-validated; it cannot grant a broader security boundary than the runtime policy.

Illustrative shape:

```yaml
testing:
  selection_mode: multi
  selected: [unit, integration, api, regression]
  recommendations:
    enabled: true
    approval_required: true
  options:
    api:
      protocols: [rest, graphql]
    regression:
      include_existing: true
      change_aware: true
execution:
  network: disabled
  timeout_seconds: 300
approvals:
  plan: required
  expanded_scope: required
  assertion_changes: required
```

This is a conceptual schema; the TAD defines the requirements for its eventual contract.

### Natural language

The parser converts a request into a proposed structured scope, targets, constraints, and unknowns. It displays the interpretation and requests confirmation before planning. Ambiguous terms, incompatible requests, or inferred extra tests must be surfaced, not guessed into authorization. Example: “Run unit and API tests on checkout; recommend security checks” selects unit/API and leaves security pending approval.

## 8. Normalized testing taxonomy

The taxonomy consolidates both supplied diagrams and the project discussion. Diagram category labels are retained as user-facing domain groupings; overlapping entries become one canonical capability with multiple tags. **Protocol, technique, test level, operational check, and agent capability are distinct dimensions.** A selectable domain may bundle several compatible types, but the registry stores each type separately.

| Canonical domain | Selectable test types / techniques |
|---|---|
| Functional and behavior | Unit; component; integration; system; end-to-end (E2E); UI; acceptance/UAT; alpha; beta; exploratory support; installation; configuration; smoke; sanity; regression; user journey; business flow; release validation. |
| Frontend and experience | UI; component; visual; accessibility; usability; responsive; cross-browser/browser compatibility; user interaction; form validation; navigation; session; frontend security; frontend performance. |
| API and service | API behavior; REST; GraphQL; SOAP; WebSocket; schema validation; contract; authentication; authorization; API security; API performance; API regression. REST/GraphQL/SOAP/WebSocket are protocol/interface selectors attached to API tests, not test levels. |
| Data and database | Data validation; integrity; consistency; schema; stored procedure; trigger; ETL; migration; backup; recovery; database performance. |
| Security | Vulnerability assessment; authorized penetration testing; authentication; authorization; dependency scanning; secrets scanning; network security; source-code security; API security; compliance checks; SAST; DAST. SAST/DAST and scanners are techniques/adapters under security. |
| Performance and capacity | Load; stress; spike; endurance; scalability; volume; concurrency; capacity; benchmark. |
| Reliability, resilience, compatibility | Reliability; availability; failover; recovery; disaster recovery; maintainability; OS compatibility; device compatibility; localization; internationalization. |
| Mobile | Android; iOS; device; network; notification; battery; permission. Mobile is a platform profile that may combine functional, compatibility, performance, or security test types. |
| Code quality | Static code analysis; code quality scanning; technical debt analysis; security code scanning; linting. These are quality checks that can produce findings without generated behavioral tests. |
| DevOps and delivery | Build validation; deployment testing; infrastructure testing; container testing; Kubernetes testing; CI/CD validation. |
| Test suite quality (cross-cutting) | Coverage; mutation testing; flakiness/repeatability; duplicate detection; assertion/oracle review; test maintenance. These evaluate tests and are run only when selected or included by an approved profile. |

### Cross-cutting agent capabilities (not test types)

Requirement analysis; test-case and test-data generation; script generation; risk-based prioritization; change-aware selection; traceability; root-cause classification; bounded self-healing; visual defect detection; report synthesis; fix suggestions; historical failure learning. “Automated bug creation” in the diagram is interpreted as **controlled fault injection/mutation in an isolated copy**, never creation of real defects in the user's application or production system.

### Normalization rules

- Component, UI, visual, accessibility, API security, authentication/authorization, recovery, and device labels can appear in multiple domains but map to one canonical type and may carry multiple domain tags.
- Regression is a selection purpose/strategy that can execute unit, API, UI, or E2E suites; it is not a separate runner.
- Smoke, sanity, release, UAT, alpha, and beta describe validation intent/context; they reference underlying executable scenarios.
- Protocols (REST/GraphQL/SOAP/WebSocket), platforms (Android/iOS), and tools (SAST/DAST/scanners) are dimensions/adapters, not interchangeable test levels.
- Exploratory testing is assisted session planning and evidence capture; autonomous execution is bounded and cannot be represented as a deterministic assertion suite alone.

## 9. Feature matrix

| Capability | MVP | Later expansion | User-visible outcome |
|---|---|---|---|
| Repository intake and detection | Local checkout; manifests; language/framework/test detection | Git provider integrations; richer monorepo support | Project profile with evidence and gaps |
| Scope selection | Multi-select CLI/config/natural language; conflict resolution | Dashboard selection and reusable team profiles | Resolved, reviewable scope |
| Taxonomy registry | Canonical IDs, aliases, domain tags, prerequisites | Community/organization extensions | Extensible catalogue without hard-coded workflow branches |
| Planning | Language-neutral scenario plan; stable IDs; approval gate | Requirement/issue import, richer risk models | Editable scenario plan before test code |
| Adapters | Python/pytest, JS/TS/Vitest, Java/JUnit 5 baseline; API/E2E adapter subset | C#, Go, mobile, QA DSLs, other ecosystems | Idiomatic generated tests and standard result data |
| Execution isolation | Containerized, resource-limited, no network by default | MicroVM-backed isolation; managed runners | Safe reproducible run with artifacts |
| Test quality | Parse results; line/branch coverage where supported; repeat-run flake signal; basic assertion checks | Mutation adapters; semantic duplicate/oracle analysis | Evidence-based acceptance status |
| Change-aware testing | Git diff to affected symbols/tests; user can request full run | Historical dependency/risk model | Recommended impacted scope with full-run option |
| Traceability | Scenario → target → generated test → execution → evidence | Requirement/issue/commit links | Clickable/auditable lineage |
| Bounded repair | Classify common failures; patch generated tests/fixtures only; capped attempts | More adapters; learned diagnosis | Reviewable repair proposal and rerun evidence |
| Reporting | Per-domain Markdown/JSON plus consolidated run report | HTML/dashboard; CI annotations | Domain details plus one summary |
| CI and MCP | CLI-first; machine-readable output; thin MCP surface after core contract | Provider-specific actions and dashboard | IDE/CI integration without duplicating engine logic |
| Security checks | Safe dependency/source checks where adapter exists; explicit target authorization | DAST, API security, compliance packs | Findings with scope and limitations |
| Performance checks | Not a default MVP execution mode; constrained profile prototype only after safe target contract | k6 and other load tools | Bounded metrics and workload assumptions |

## 10. Functional requirements

- **FR-01:** Import a local repository and identify root, languages, frameworks, manifests, existing tests, and relevant project metadata.
- **FR-02:** Resolve multiple selected testing types from CLI, config, and natural language into one canonical scope document.
- **FR-03:** Detect prerequisites and label each selected type supported, partial, or unsupported with reasons.
- **FR-04:** Recommend additional test types with rationale, prerequisites, estimated scope, and risks; do not execute them until explicit approval is recorded for that run.
- **FR-05:** Generate a language-neutral, stable-ID test plan with targets, preconditions, data needs, priority, expected outcomes/assertions, and source evidence.
- **FR-06:** Pause at the configured human approval gate before test generation/execution; preserve approved plan revision and approver context.
- **FR-07:** Apply a pre-flight language-boundary rule: white-box unit tests must use the target module language and compatible ecosystem; black-box API/E2E/performance tests may use a user-preferred supported language against an isolated running target. Report any exception and its reason.
- **FR-08:** Generate tests only through registered adapters and write changes to a reviewable, isolated output area.
- **FR-09:** Execute only approved tests in a sandbox with policy-enforced commands, resource limits, network policy, and cleanup.
- **FR-10:** Collect standardized results, logs, traces, coverage, test artifacts, and adapter/environment metadata.
- **FR-11:** Evaluate assertion strength, coverage deltas, repeatability, and mutation evidence when configured and supported; separate missing evidence from failure.
- **FR-12:** Classify failures into test defect, application behavior mismatch, plan ambiguity, environment/setup, timeout/resource, or flaky result where evidence permits.
- **FR-13:** Limit repair attempts to configured 3–5 maximum; default proposal cap is 3 per affected scenario. Never change assertions, add skips, alter expected behavior, or modify application business logic without required approval.
- **FR-14:** Maintain traceability from source symbol/requirement/change through scenario, generated test, run, result, and report evidence.
- **FR-15:** Support change-aware impact analysis and always allow the user to expand to a full suite.
- **FR-16:** Emit an individual report per selected domain and one consolidated report; make unsupported, skipped, failed, and unapproved-recommended coverage explicit.
- **FR-17:** Preserve run history and configuration/policy snapshots sufficient to reproduce or explain the result.
- **FR-18:** Support safe interruption, resume, and cancellation without leaving processes, containers, credentials, or fixtures behind.

## 11. Quality gates and acceptance states

Generated tests are not accepted solely because they pass. Per-test/per-suite status is one of:

- **Accepted:** Meets configured execution, assertion, reliability, and applicable evidence thresholds.
- **Needs review:** Runs but evidence is insufficient, thresholds are unavailable, expected behavior is ambiguous, or only partial validation completed.
- **Rejected:** Fails, is materially flaky, violates policy, or has demonstrably weak/invalid assertions.

Quality signals include syntax/import validation, framework discovery, meaningful assertions, line/branch coverage delta, mutation score where supported, repeated-run consistency, duplicate/overlap signal, and deterministic fixture behavior. Thresholds are project-configurable and must be reported with their source. Missing instrumentation is “not measured,” never zero or pass. A mutation score is one signal and does not prove correctness; equivalent mutants and unsupported constructs must be identified/qualified.

Run-level gate reports selected scope completion, per-domain outcomes, unresolved prerequisites, policy violations, and evidence completeness. The product must not present an overall green status if a selected domain did not run; use an explicit partial/incomplete status.

## 12. Reporting requirements

Each domain report includes: selected types and options; plan revision and approvals; target and environment; tests generated/reused; pass/fail/skipped/unsupported counts; duration; quality metrics; failure classifications; repair attempts and diffs; artifacts/evidence links; limitations and recommendations.

The consolidated report includes: run identity; repository revision/change set; selected and approved scope; unapproved recommendations; per-domain status; cross-domain summary; overall completion status; quality-gate result; key failures/risks; links to each domain report and raw machine-readable evidence. Reports are available in Markdown and JSON in MVP. Sensitive values are redacted.

## 13. Success measures

- Scope resolution fidelity: explicit requested types are retained or visibly blocked; no silent omission.
- Plan approval usability: reviewers can understand target, expected behavior, and rationale before generation.
- Traceability completeness: each generated test and result points to a scenario and target or states why it cannot.
- Reproducibility: same revision/config/adapter image yields explainable, stable results within known nondeterminism limits.
- Safety: zero out-of-policy executions in defined acceptance scenarios; clean teardown on success, failure, timeout, and cancellation.
- Test usefulness: meaningful assertion and mutation/coverage evidence improve over baseline where measurable; no single metric substitutes for review.
- Report completeness: one domain report per selected domain plus a consolidated report for every completed/partial run.
- Adapter quality: adapter contract conformance and clear unsupported state for missing capabilities.

## 14. Risks and assumptions

| Risk / assumption | Impact | Mitigation / decision |
|---|---|---|
| Weak test oracles create false confidence | Critical | Plan expected behavior first; assertion review, coverage/mutation/repeatability signals; transparent limitations. |
| Untrusted repositories or dependencies attack runner | Critical | Defense-in-depth sandbox, no secrets, network off, resource controls, command allowlist, cleanup; evaluate stronger isolation for hosted use. |
| Language/framework scope expands too quickly | High | Registry from day one; narrow validated MVP adapters; publish support matrix. |
| Environment drift makes tests flaky | High | Deterministic images/seeds, pinned dependencies where feasible, repeat runs, environment metadata. |
| Natural-language intent is ambiguous | High | Display structured interpretation; ask/stop at approval boundary. |
| “Autonomous healing” masks application defects | High | Repair only generated artifacts by default; never weaken assertions to green; approval for sensitive changes. |
| Taxonomy mixes levels, protocols, tools, and capabilities | Medium | Canonical type IDs plus dimensions/tags; preserve aliases for discoverability. |
| User assumes security/performance report is exhaustive | High | State target authorization, selected scope, tool coverage, workload assumptions, and limitations. |
| Project is expected to test production | High | Production target disabled by default; explicit target allowlist and authorization required for any live environment. |
| Long-term history could expose source or secrets | Medium/High | Minimize stored content; redact; configurable retention; access control in hosted deployment. |

Assumptions: initial delivery is CLI-first and repository-local; Docker-compatible isolation is available for the first execution path; target code may be untrusted; organization-specific policy can further restrict capabilities; language and framework support grows in tiers rather than shipping all requested ecosystems at once.

## 15. Out of scope for this decision record

Specific LLM provider/model, final license, hosted multi-tenant deployment design, billing, UI visual design, exact coverage/mutation thresholds, and enterprise compliance certifications remain open and must be decided before the relevant implementation phase.

