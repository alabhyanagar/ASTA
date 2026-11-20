# Product Requirements Document
## Autonomous Software Testing Platform (ASTA)

**Version:** 1.0  
**Status:** Product baseline approved for reference; technology choices marked proposed remain subject to validation  
**Date:** 2026-11-18  
**Implementation status:** Not started

## 1. Product summary

ASTA is a locally installed, user-directed software testing application with an agent workflow and an MCP integration option. It inspects a codebase or explicitly authorized running target, identifies supported checks, helps the user select and approve a testing scope, creates a reviewable test plan, generates or configures tests through adapters, executes approved checks in an isolated worker, evaluates results from evidence and explicit expectations, and produces per-domain reports plus one consolidated report.

AI may assist with analysis, scenario planning, bounded script generation, and evidence-linked explanations. Deterministic application code assigns test statuses. The product never treats an AI opinion as a verified pass/fail, silently expands user scope, or executes arbitrary model commands.

## 2. Problem and opportunity

Testing an existing application requires understanding its structure, choosing the right test layers and tools, configuring environments, creating useful assertions, and consolidating evidence. Existing projects also differ in language, frameworks, commands, API schemas, data fixtures, and risk. ASTA reduces that manual work while keeping test scope, authorization, expectations, and verdicts reviewable.

## 3. Target users

- **Developer / project owner:** inspect a project, select focused checks, review test plans/findings, rerun checks, decide whether to apply a patch.
- **QA engineer:** define workflows, expected behavior, thresholds, accounts, and test scope; review domain outcomes.
- **Security reviewer:** authorize targets and risk classes for source, dependency, API, and active security checks.
- **Performance engineer:** define target, workload, thresholds, traffic ceilings, and duration.
- **Administrator:** configure providers, execution policy, secrets, retention, and later integrations.
- **Engineering lead:** review domain outcomes, gaps, risks, and evidence in a consolidated report.

## 4. Product goals and success measures

### Goals

1. Reduce manual effort to identify and run relevant checks.
2. Generate or configure reproducible tests from code, schemas, formal specifications, and user-provided workflows.
3. Produce deterministic, evidence-based statuses and expose uncertainty and untested scope.
4. Provide prioritized findings and evidence-linked improvement suggestions.
5. Add testing capability through adapters without coupling tools to the evaluator.
6. Protect source, credentials, test data, and target systems.

### Success measures (thresholds TBD)

- Defect recall on a planted-defect benchmark (“bug garden”).
- False-positive rate, duplicate-finding rate, and flaky rate.
- Accuracy of Blocked/Unsupported/Inconclusive reporting.
- Reproducibility and evaluator agreement for identical evidence.
- Execution time, local-model latency/memory, and AI-on versus AI-off quality.
- Sandbox and egress proof points, secret-redaction results, cancellation/cleanup behavior.
- User ability to understand scope, expectation source, and evidence from the CLI and later UI.

## 5. Product principles and business rules

- **User-directed scope:** users select one or more test types; selection is multi-select.
- **Applicability is not authorization:** the system may identify checks applicable within approved scope. Additional check types remain recommendations until explicitly approved.
- **Plan before code:** present a versioned plan with expectation provenance and limits before generation/execution.
- **Deterministic verdicts:** only user criteria, formal specifications, existing tests, configured thresholds, or defined universal checks can produce Passed/Failed. An AI-only expectation is Inconclusive.
- **Evidence and uncertainty:** every finding cites evidence; AI hypotheses are labeled inferred with confidence or unknown.
- **Safe defaults:** no network by default, no host secrets, no target widening, no arbitrary shell, no unbounded repair.
- **Honest scope:** reports state included, excluded, blocked, unsupported, not applicable, not measured, and awaiting authorization checks.
- **One canonical check, many tags:** overlapping taxonomy labels should not cause duplicate execution when target, operation, and assertion are equivalent.

## 6. User workflow

1. Create project; provide repository/folder/archive or explicitly authorized target; set scope and environment.
2. Validate source/archive, target, authorization manifest, and scope before inspection/network access.
3. Inspect project; record detected facts and evidence separately from interpretations.
4. Select multiple testing types through CLI/config/natural language; view applicability and prerequisites.
5. Review optional recommendations. Approve or decline exact additions; no unapproved recommendation runs.
6. Generate a plan with target, assertion/expectation source, risk, limits, and resource needs.
7. Review/edit/approve or exclude checks; high-risk checks wait for their own authorization.
8. Prefer existing tests, formal schemas, or deterministic generators; use bounded AI assistance where configured.
9. Validate scripts and target scope; execute approved checks in isolated worker.
10. Evaluate attempts deterministically; retain all attempts and evidence.
11. Analyze/group findings with evidence-linked hypotheses; compare runs when requested.
12. Report statuses, gaps, limitations, and recommendations; enter optional fix mode only after explicit authorization.

## 7. Feature inventory and priority

### Must-Have / M1 foundation

- Local project intake; source/revision provenance; safe archive validation.
- Multi-select testing scope via CLI and `.testagent.yaml`; natural-language scope selection is accepted, but M1 versus later timing remains open and every channel must resolve to the same normalized scope model.
- Authorization manifest with allowed targets/actions and per-check risk approval.
- Inspector and capability registry with applicability states and evidence/confidence.
- Plan review/edit/approval; expectation provenance; include/exclude reasons.
- Project-native test execution and initial supported test adapters.
- Script validation, path/scope checks, source-outside-by-default generation.
- Isolated worker with deny-by-default egress, time/resource limits, cancellation, cleanup, and trusted-project restriction until security boundary is proven.
- Deterministic evaluator, attempt history, reproducible run state, audit trail.
- Findings with source/evidence and severity; Markdown and versioned JSON reporting.
- Both per-domain reports and consolidated report.
- CLI: project add, inspect, plan, approve, run, status, cancel, rerun, report.
- AI-off usable pipeline and strict boundary between AI and evaluator/worker/reporter.

### Must-Have / M2 AI and core adapters

- Schema-validated AI gateway, bounded inputs, invalid-output retries, degradation/fallback.
- Local Ollama is proposed first; remote compatible providers remain optional and off by default pending policy.
- REST schema/contract and API checks, with authentication/authorization when criteria are supplied.
- Web checks: crawl/navigation/forms/responsive/accessibility and evidence capture.
- Static code/security, secrets, dependency, and code-quality checks where adapters are verified.
- AI claims linked to evidence and marked inferred/confirmed.

### Later / M3 and beyond

- REST API and React/TypeScript web UI over the same core services.
- Run comparison and richer analyzer/finding aggregation.
- Bounded Locust or equivalent performance adapter; passive ZAP.
- HTML/JUnit XML/SARIF exports when adapter and schema support are verified.
- Database testing, visual baselines, cross-browser, GraphQL/WebSocket/SOAP, fuzz/property/mutation, container/Kubernetes, fix mode, CI integrations, multi-user roles, Android/mobile.
- Hosted or multi-worker deployment only after isolation, persistence, authorization, and scale requirements are defined.

## 8. Testing catalogue

Domains and examples:

1. **Existing project / functional:** unit, component, integration, system, E2E, acceptance/UAT, regression, smoke, sanity, exploratory, installation, configuration, alpha/beta, business flows, release validation.
2. **API/service:** REST, GraphQL, SOAP, WebSocket, schema/contract, auth/authz, boundary/error, regression, security, and performance checks.
3. **Web/frontend:** crawl, navigation, forms, sessions, user journeys, responsive, accessibility, screenshots/visual, cross-browser, frontend performance/security.
4. **Database/data:** validation, integrity, consistency, schema, stored procedures, triggers, ETL, migrations, backup, recovery, performance.
5. **Security:** static analysis/SAST, secrets and dependency scanning, vulnerability assessment, API security, DAST, authorized active scan/fuzz/penetration, compliance criteria evaluation.
6. **Performance:** load, stress, spike, endurance, scalability, volume, concurrency, capacity, benchmark.
7. **Reliability/compatibility:** reliability, availability, failover, recovery/disaster recovery, maintainability, OS/device/browser, localization/internationalization.
8. **Mobile:** Android, iOS, device, network, notification, battery, permission (requires device/emulator support).
9. **Code quality:** static analysis, quality scan, technical debt, security code scan, lint.
10. **DevOps/delivery:** build, deployment, infrastructure, container, Kubernetes, CI/CD validation.
11. **Test suite quality:** coverage, mutation, flaky/repeatability, duplicate detection, assertion/oracle review, suite maintenance.

Taxonomy normalizes protocols, platforms, techniques, validation intent, and capabilities as dimensions. “Automated bug creation” means controlled isolated fault injection/mutation, never a real defect in the target. Exploratory testing is assisted session planning/evidence capture; regression is a strategy over underlying suites.

## 9. Out of scope

- Guaranteeing software is bug-free, secure, compliant, or release-ready.
- Replacing human acceptance, usability research, accessibility expert review, or professional penetration testing.
- Unrestricted security scans, destructive tests, or high-volume load without authorization.
- Supporting every language, framework, OS, device, database, or deployment platform initially.
- Changing original application source by default.
- Using AI model opinion alone for a final verdict.

## 10. Product acceptance baseline

- A user submits a supported project, inspects its profile, reviews/approves a plan, runs approved checks, and opens a report from CLI.
- Planted-defect benchmark records tool/script versions, plan, attempts, evidence, and report sufficient for replay without another model call.
- Out-of-scope targets, unauthorized checks, missing prerequisites, unsupported adapters, and unavailable sandbox are explicitly handled.
- Evaluator golden cases cover all statuses, provenance, retries, verdict rules, and timeout handling.
- No result passes solely from model output.
- Reports show scope, assumptions, status counts, gaps, evidence, and limitations; each selected domain has a report and the run has a consolidated report.
- Security, privacy, retention, license, and performance proof points are completed before corresponding product claims.

## 11. Open product decisions

Initial OS/hardware/container runtime; archive limits; project/package name; exact local-model selection; user-approved retry/flaky policy; severity mapping; quality thresholds; remote AI opt-in UX; retention and encryption; product/tool/model licensing; production-target policy; REST/API authentication and multi-user roles; performance traffic ceilings; latency/concurrency availability targets; hosted deployment model; and specific adapters/versions.

