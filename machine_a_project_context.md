# Autonomous Software Testing Agent — Complete Project Context

**Document purpose:** Lossless technical state extracted from the project discussion, the supplied testing taxonomy diagrams, and the current PRD/TAD drafts.  
**State date:** 2026-11-18  
**Implementation:** Not started. The project discussion explicitly said not to code until product/architecture decisions and documentation are finalized.  
**Terminology:** “Confirmed” means explicitly accepted/locked by the user or consistently required in the project brief. Candidate technologies remain proposals unless marked selected.

## 1. Executive Overview & Core Objective

### Problem statement

Build an AI-powered autonomous software testing agent that accepts an existing application codebase, analyzes structure and dependencies, generates human-reviewable test plans, writes executable tests, runs them in isolated sandboxes, evaluates whether tests are useful, and performs bounded self-healing across supported testing layers.

The product is more than an AI test-case generator. It is a controlled workflow for repository understanding, user-selected scope, language-neutral planning, language/framework-specific generation, isolated execution, test-quality evidence, bounded repair proposals, and traceable reporting. Deterministic parsers, runners, coverage tools, and policy checks should do work deterministically; AI assists where reasoning or synthesis is useful.

### Target users and jobs

- **Application developers:** select unit/component tests for changed code, inspect proposed cases and patches, get actionable feedback.
- **QA engineers:** combine API, integration, E2E, regression, exploratory support, and acceptance checks; track scenario outcomes.
- **Security engineers:** select approved source/dependency/API/dynamic checks within an authorized target boundary.
- **Performance engineers:** generate bounded workload scenarios and compare latency, throughput, and error rates in an approved environment.
- **Release engineers:** run smoke, sanity, compatibility, deployment, and release validation with go/no-go evidence.
- **Engineering leads:** review consolidated quality, coverage, risk, and unresolved limitations across domains.

### Primary success criteria

1. Requested test types are explicitly resolved; no selected type is silently omitted.
2. Additional recommendations never become execution authorization without explicit approval.
3. Plans, generated tests, executions, repairs, and results have traceable evidence.
4. Test usefulness is assessed beyond “it passed,” using meaningful assertions, coverage, mutation where supported, and repeatability.
5. Untrusted code runs only within enforceable isolation and policy limits.
6. A run produces an individual report for every selected testing domain and one consolidated report, including incomplete/unsupported states.
7. A narrow MVP can complete an end-to-end slice safely; broad taxonomy/language coverage grows through adapters.

## 2. Product Requirements (PRD State)

### Confirmed product decisions

| Decision | Locked behavior |
|---|---|
| Testing selection | **Multi-select** testing types/domains; users can combine types in a single run. |
| Additional recommendations | Agent can recommend additional tests, but **explicit user approval is required before execution**. A recommendation is not authorization. Approval is scoped to the run and exact added types. |
| Reporting | **Unified reporting:** individual domain reports plus one consolidated report. |
| User control | User specifies desired testing types (e.g. unit, integration, regression). Agent must not independently run every possible test. |
| Planning | Language-neutral structured plan precedes test generation; human review/approval gate is required by default. |
| Additional features | User accepted all features proposed in the prior architecture discussion, including change-aware testing, regression impact analysis, traceability, deduplication, risk-based selection, historical failure learning, CI/CD integration, and test-suite maintenance. Delivery is phased; acceptance does not mean every feature ships in MVP. |
| Implementation | Documentation/architecture first; no coding or implementation started. |

### Confirmed features and user stories

Priorities: **Must-Have** means core product contract/MVP prerequisite. **Nice-to-Have** means accepted product scope with later/phased delivery unless a later decision promotes it.

#### Must-Have

- **Repository intake and analysis:** As a user, I can point the agent at an existing local repository/Git checkout and see detected languages, frameworks, dependencies, structure, existing tests, APIs/schemas where discoverable, and analysis limitations.
- **User-selected multi-scope:** As a user, I can select multiple testing domains and individual test types using CLI flags, `.testagent.yaml`, or natural language.
- **Capability validation:** As a user, I see each selected type marked supported, partially supported, or unsupported with reasons/prerequisites; unsupported selections are never silently skipped or substituted.
- **Approved recommendations:** As a user, I can review recommendations with rationale, prerequisites, risk/cost, and expected evidence, approve or decline them, and know that pending recommendations will not execute.
- **Neutral test planning:** As a reviewer, I can inspect/edit scenarios before code generation; each scenario has stable ID, target, evidence, preconditions, fixture/data needs, priority, and intended assertions/outcomes.
- **Language/framework boundary:** White-box unit tests use the target module’s source language and compatible ecosystem; black-box API/E2E/performance tests may use a user-selected supported language against a running isolated application. Component/integration scenarios are explicitly classified white-box or black-box.
- **Adapter-based generation/execution:** Tests are generated and run only through registered adapters and policy-validated commands; generated files are reviewable.
- **Sandboxing:** Untrusted source, generated tests, install hooks, and outputs run under filesystem, network, identity, resource, timeout, secret, and cleanup controls.
- **Quality evidence:** Evaluate assertion quality, line/branch coverage where supported, repeatability/flakiness, mutation evidence when selected/supported, duplicate overlap, and fixture determinism. Missing metric means “not measured,” never pass or zero.
- **Bounded repair:** Failure diagnosis precedes repair. Repairs are limited (3–5 max; recommended default 3 per affected scenario), reviewable, and cannot silently weaken assertions or modify app behavior.
- **Traceability:** Preserve `source/requirement/change → target → scenario → generated test → run/result → report evidence`.
- **Change-aware option:** Recommend impacted tests based on changes, confidence, and dependency evidence; always retain user option to run full suite.
- **Reports:** Per selected domain plus consolidated run report in Markdown and JSON; show selected/pending/declined/unsupported/skipped/failed scope and evidence.
- **Run lifecycle:** Durable state, approval interrupts, resume/cancel, idempotency, and cleanup across success/failure/timeout/cancel.
- **CLI-first product:** Modular standalone CLI and containerized CI runner; thin MCP surface shares core use cases.

#### Nice-to-Have / Accepted Later Scope

- Richer monorepo and Git provider support.
- Web dashboard, HTML reports, CI annotations, reusable team profiles.
- Additional language/framework adapters beyond initial core.
- Mobile emulator/device execution; QA DSL execution.
- Advanced semantic deduplication/oracle review and historical failure learning.
- Broader mutation testing, advanced risk models, requirement/issue import.
- Security (SAST/DAST/API security/compliance) and constrained performance/load adapters.
- Hosted managed runners, MicroVM isolation (gVisor/Firecracker), stronger enterprise controls.
- Defect-ticket integrations only with explicit user-configured policy.

### Explicit Non-Goals / Out-of-Scope items

- A passing run does not prove application correctness or security.
- No arbitrary generated script execution on host or against production.
- No autonomous app business-logic changes, assertion weakening, or “make it green” behavior.
- No promise to support every language, framework, mobile device, CI provider, or scanner in first release.
- Not a replacement for dedicated penetration test, compliance audit, usability study, or performance lab.
- No automatic external defect ticket creation/publication absent explicit integration policy.
- No implementation now; current task is architectural/product documentation.

### Business rules and workflows

#### End-to-end workflow

`Import project → Analyze repository → Select scope → Resolve prerequisites/support → (Recommend additions, pending approval) → Build neutral plan → Human review/approval → Generate tests → Execute in sandbox → Quality/evidence evaluation → (bounded repair and rerun) → domain reports + consolidated report`.

Detailed rules:

1. Static analysis should not execute project modules.
2. Scope may come from CLI, config, and natural-language request. All resolve into one canonical versioned scope model.
3. Runtime safety policy is a hard ceiling. Suggested precedence: `runtime safety policy → explicit per-run CLI/user request → project config defaults → profile defaults`.
4. Natural language is parsed into a proposed scope and shown for confirmation; ambiguity is surfaced rather than guessed into authorization.
5. Recommendations include rationale, evidence, risks, cost/prerequisites, and state `pending/approved/declined`. Approval binds to run and exact canonical type IDs.
6. Scope states: `Supported`, `Partially supported`, `Unsupported`. No silent omission or substitution.
7. Plan approval binds to run ID, scope revision, plan revision, and hash; a changed plan/scope invalidates approval.
8. A `--yes`-style switch cannot override policy-required scope-expansion or sensitive-change approvals.
9. Generated tests are not permanent/accepted simply because they pass. Status: `Accepted`, `Needs review`, `Rejected`.
10. Missing instrumentation/evidence is “not measured,” not zero or pass. Partial selected-domain execution cannot be labeled overall green.
11. “Automated bug creation” in supplied diagram is interpreted as controlled fault injection/mutation in isolated copy, never real defects in user app/production.
12. Regression is a selection purpose/strategy reusing underlying unit/API/UI/E2E tests, not a separate runner.
13. Smoke/sanity/release/UAT/alpha/beta are validation intent/context referring to executable scenarios.
14. Exploratory testing is assisted session planning/evidence capture, not purely deterministic assertion execution.

#### Selection interfaces

CLI examples (illustrative, not implemented):

```text
testagent run --types unit,integration,api,regression
testagent run --types performance,security --profile production-readiness
testagent plan --request "Test payment and authentication with API and integration tests"
```

Earlier discussion also showed:

```bash
testagent run \
  --types unit,integration,api,regression

testagent run \
  --types performance,security \
  --profile production-readiness
```

Config example (illustrative; schema not finalized):

```yaml
project:
  name: sample-application
  root: .

testing:
  selection_mode: manual
  selected:
    - unit
    - integration
    - api
    - regression
  options:
    unit:
      enabled: true
    integration:
      enabled: true
    api:
      protocols: [rest, graphql]
    regression:
      include_existing_tests: true
      include_generated_tests: true
    performance:
      enabled: false
    security:
      enabled: false

analysis:
  tree_sitter: true
  dependency_graph: true
  repo_map: true
  max_context_tokens: 12000

generation:
  source_language: auto
  unit:
    language: auto
    framework: auto
  integration:
    language: python
    framework: pytest
  e2e:
    language: typescript
    framework: playwright
  performance:
    enabled: false
    framework: k6

execution:
  sandbox: docker
  timeout: 300
  max_retries: 3

quality:
  line_coverage_target: 70
  branch_coverage_target: 60
  mutation_testing: true

approval:
  test_plan: required
  source_code_changes: required
  assertion_changes: required
```

Another shorter candidate config from the PRD:

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

Natural language example: “Test the authentication and payment modules. Perform unit, integration and API testing. Also identify potential security issues.” Agent converts request into structured proposed scope, displays it, and holds security expansion pending approval.

## 3. System Requirements (SRS State)

### Functional requirements by module/component

#### Project input and repository intelligence

- Accept local directory / existing Git checkout; Git repository import/clone is envisioned, exact remote-auth flow not selected.
- Detect languages, frameworks, dependencies/packages, project/build/test structure, symbols/functions/classes/methods, calls/imports, APIs/routes/OpenAPI, database schemas/migrations, and CI descriptors where possible.
- Use Tree-sitter/AST extraction, dependency graph, RepoMap ranking/PageRank, and bounded context retrieval; do not dump entire repo or rely only on naive vector RAG.
- Exclude VCS internals, generated outputs, binaries, configured paths, and secrets; handle malformed source with partial analysis status.
- Support token budget; one earlier example set `max_context_tokens: 12000`.
- Change-aware analysis maps Git diff to symbols/callers/tests/dependency edges; disclose confidence and uncertainty; full-suite remains selectable.

#### Scope and taxonomy resolver

- Resolve CLI/config/natural language/profile into canonical IDs, aliases, options, selection source, scope hash, support state, prerequisites, resolved adapter, conflicts, unresolved questions.
- Multi-select domains/types; include/exclude and per-type options envisioned.
- Each taxonomy record has canonical ID/name/aliases/domain tags; dimensions (`test_level`, `protocol`, `platform`, `technique`, `validation_intent`, `quality_check`); prerequisites; supported targets; risk/side-effect profile; adapter/quality/report capabilities; version/deprecation.
- Additional tests remain recommendations pending user approval.

#### Planning and approval

- Produce language-independent structured Markdown plans in `specs/*.md` (specific earlier proposal) with stable scenario IDs, target, objective, edge cases, preconditions, test data, priority, expected assertions, language binding deferred.
- Example schema content from discussion: target `DiscountService.calculateDiscount()`; objective verify discount calculations/input validation; TC01 valid 10% => correct discounted price; TC02 zero => original price; TC03 100% => zero; TC04 negative discount => validation error; TC05 >100% => validation error; TC06 negative product price => validation error; TC07 null => appropriate exception; priority High; layer Unit; assertions return values/validation errors/exceptions.
- Human approval required before generation/execution by default; approval revision/hash invalidation rules apply.

#### Generation and adapters

- Use one shared planning/generation interface with pluggable adapters, not a separate AI agent for every language/testing domain.
- Adapter operations include detection, config validation, generation, dependencies/environment, structured test commands, coverage command/parser, result parser, test discovery, capabilities, and repair hints.
- Generate only from approved neutral plan; retain scenario IDs in test metadata/names.
- Keep generated artifacts in reviewable separate area; validate paths/diff before execution.
- User may choose test language/framework by `.testagent.yaml`, CLI flags, or natural language.

#### Execution, data fixtures, and reporting

- Containerized isolated execution, databases/services fixtures, browser automation, logs/traces/artifacts.
- Proposed Docker SDK for Python / Docker Compose / Testcontainers; none irrevocably selected.
- Application/test sidecar containers when test language differs from app language; private network, controlled endpoints/fixtures.
- Standardize results, logs, traces, coverage, mutation, artifacts and environment metadata.
- Produce individual domain report plus consolidated run report; Markdown and JSON specified in current PRD/TAD.

#### Quality, mutation, and repair

- Quality signals: meaningful assertion inspection, line/branch coverage delta, mutation testing, repeated execution/flakiness, behavioral consistency, duplicate tests, fixture determinism.
- Earlier proposed mutation score formula:

  `Mutation Score = (Killed Mutants / Valid NonEquivalent Mutants) × 100`

  Equivalent mutants are not test failures; mutation score is a signal, not proof.
- Failure classes: import/syntax, missing dependency, fixture/setup, app startup, assertion failure/behavior mismatch, timeout/resource, flakiness, environment, policy violation, ambiguous plan.
- Bounded repair cap hard max 5; recommended/default 3 per affected scenario and global/time budget. Never simply change assertion expected value to pass (example bad change: `assert result == 90` to `assert result == 100`). Assertion changes, skips/xfail, expected behavior changes, app code changes, threshold weakening need exact human approval; application business logic not auto-patched in MVP.
- Stop on identical repeated failure, exhausted budget, policy denial, ambiguous expected behavior, or nondeterministic diagnosis.

#### State, safety and lifecycle

- Durable graph workflow with checkpoints, approval interrupts, retry policies, execution history; idempotency key per run/stage/revision/adapter invocation.
- Safe interruption/resume/cancellation; termination of processes/containers; revoke ephemeral credentials; remove temporary volumes/network; record cleanup status.
- Resume validates repository revision, policy/taxonomy/config/adapter image and plan hashes; material changes require reanalysis/approval.

### Non-functional requirements

#### Security

- Treat repo, generated code, dependencies/install hooks, command output, DOM snapshots, and artifacts as untrusted.
- Source read-only; separate writable generated-test area; no host home, Docker socket, or sensitive host paths.
- Non-root user; drop unnecessary capabilities; read-only root filesystem where feasible; seccomp/AppArmor equivalent.
- Network disabled by default; per-run private sidecar network; explicit destination allowlist. Production access disabled by default and never inferred from repository URL/config.
- No wholesale host environment/secrets; scoped short-lived test credentials, redaction, revocation.
- CPU/RAM/PID/disk/output/wall-clock limits; process-group termination on timeout.
- Structured argv/command IDs, no model-supplied shell interpolation; policy validation and command audit.
- Synthetic/sanitized fixture data; isolated disposable DB; prevent external writes.
- Scan/size-limit/redact artifacts and logs; cleanup resources on all exit paths.
- Threats: prompt injection in repo docs/source, command injection, malicious package scripts, container escape, SSRF, exfiltration, secret leakage, DoS, destructive fixtures, malicious report files, cross-run contamination.
- Docker is not itself a complete security boundary; evaluate gVisor/Firecracker/MicroVM for hosted/high-risk execution.

#### Reliability, reproducibility, and operability

- Deterministic images/seeds/fixtures; pin dependencies where feasible; capture repository revision, config/policy/taxonomy versions, adapter/image digest, prompt/template/model metadata as permitted, dependency lock IDs and seed.
- Structured logs include run ID/stage/domain/adapter/correlation ID, never secrets/full source by default.
- Metrics for stage/execution duration, resource usage, adapter failures, retry/cleanup failures, partial runs, reports.
- Health separates orchestration, runner, adapter readiness.
- Bounded concurrency per user/machine/adapter; no distributed queue until workload evidence requires it.
- Timeout, cancellation, cleanup evidence for every long-running stage.

#### Latency, throughput, availability, compliance

- No numerical latency, throughput, availability/SLA, or compliance certification requirements were finalized.
- Required resource/time bounds exist conceptually: hard wall-clock timeout, CPU/RAM/PID/disk/output limits; config example uses `timeout: 300` seconds and `max_retries: 3`.
- Initial scope is CLI/local-first; hosted multi-tenant availability and compliance remain open decisions.
- Security/compliance checks are test capabilities; they do not constitute certification.

### Input/output specifications, validation rules, and edge cases

#### Inputs

- `RunRequest`: project ref/local path/repository identity; revision/change base; selected canonical types/domains/options/excludes and source (`cli`, `config`, `natural_language`, `profile`); source/test language preferences; target environment ref (not raw secrets); approval/execution/quality policy refs; optional user request text.
- `.testagent.yaml`: project, testing selection, options, analysis, generation, execution, quality and approval settings. Schema remains conceptual/not finalized.
- Config examples above are illustrative only; the earlier values (`line_coverage_target: 70`, `branch_coverage_target: 60`, `mutation_testing: true`) were examples, not confirmed thresholds.

#### Outputs / records

- `ResolvedScope`: taxonomy version; selected types; support/prerequisite/adapter/options/reason per type; recommendation states; conflicts/questions; scope hash.
- `TestScenario`: stable ID/type/domain; source target/evidence locations; intent; preconditions; fixture/data needs; edge cases; expected assertion intent; priority/risk/dependencies/provenance.
- `GeneratedArtifact`: scenario IDs, path, digest, adapter/version, patch provenance.
- `ExecutionEvidence`: normalized status, runner/environment digest, times, command identity, stdout/stderr/artifact refs, coverage/mutation/resource usage, cleanup state.
- `DomainReport`, `RunReport`: selected types, plan revision/approvals, support/execution states, metrics/failures/repairs/evidence/limitations; consolidated report links domain reports and raw evidence.

#### Edge cases and validation

- Android selected for Spring Boot-only backend → unsupported with explanation; may offer API alternative but not substitute without approval.
- Missing API target/schema, DB fixture, browser/mobile runtime, target allowlist, test framework, or adapter → partial/unsupported, with explicit prerequisite.
- Unit test language differs from target module source → fail preflight/request compatible choice. Black-box API/E2E/perf may differ if supported and isolated.
- Component/integration ambiguous boundary → classify per scenario; do not infer only from label.
- Natural language ambiguity/conflicting CLI/config/profile → present resolved interpretation/conflict and pause.
- Recommended test unapproved → do not execute, and report as pending/declined.
- Plan/scope modified after approval → prior approval invalid.
- Missing coverage/mutation parser → “not measured,” not pass/zero.
- Selected domain did not run → overall status partial/incomplete, not green.
- Assertion failure might be app defect, bad generated test, wrong plan, environment issue, timeout, or flake; classify with evidence; do not alter oracle to force success.
- Equivalent mutants excluded from denominator; unsupported mutation constructs explicitly qualified.
- Production URL discovered in source/config does not grant target authorization.
- Cancellation/timeout must not leave processes/containers/secrets/fixtures behind; cleanup failure recorded.
- Logs and report artifacts may contain hostile content/secrets; treat as untrusted, size-limit, scan, redact.

## 4. Technical Architecture (TAD State)

### Confirmed tech stack (languages, frameworks, databases, queues, hosting/infra)

#### Confirmed product/architecture choices

- Standalone modular CLI and containerized CI/CD runner as primary form factor.
- Thin MCP server as integration interface; it is not the test engine.
- Stateful graph orchestration with durable checkpointing and human approval interrupts; **LangGraph was proposed**.
- Tree-sitter/AST, dependency graph, RepoMap/PageRank-ranked symbol selection, strict token budget; vector DB/semantic retrieval optional supplemental, not primary source of code understanding.
- Language-neutral plan before test language-specific generation.
- Pluggable adapter registry.
- Docker baseline; stronger MicroVM isolation evaluated later.
- Sidecar application and test containers for black-box cross-language tests.
- Exact persistent DB, queue, hosting, deployment topology, provider/model, and runtime are not finalized. Initial local-first filesystem/artifact store may suffice; no distributed queue until workload needs justify it.

#### Proposed language/framework/tool tiers (not all implemented or irrevocably chosen)

| Tier | Proposed support |
|---|---|
| Tier 1 Core | Python (`pytest`, `Playwright`); TypeScript/JavaScript (`Vitest`, `Playwright`); Java (`JUnit 5`, `RestAssured`). Earlier priority order: Python/pytest, JS/TS/Vitest, Java/JUnit 5, Python/JS/TS Playwright, Java/RestAssured. |
| Tier 2 Enterprise/cloud/ecosystem | C# (`xUnit`, `Playwright for .NET`); Go (`go test`, `Testify`); Kotlin, Swift, Dart, Ruby, PHP. Mobile requires device/emulator capability beyond language support. |
| Tier 3 QA DSL | Robot Framework (`.robot`), Gherkin (`.feature`), Karate DSL. Gherkin requires step-binding runtime to execute. |
| Cross-cutting | k6; Semgrep, Bandit, Trivy, OWASP ZAP as potential scanner integrations; coverage and mutation tools. No final scanner/mutation tool selection. |

Earlier discussion mentioned Python mutation examples `mutmut` or `Cosmic Ray`, JS/TS `Stryker`, Java `PIT`; not final tool selections. Earlier proposed Docker SDK for Python, Docker Compose, SQL scripts/Alembic/Testcontainers, Playwright, Python subprocess + Docker events, JUnit XML/JSON; also not all final commitments.

### System architecture & component interactions

```text
User (CLI / .testagent.yaml / natural language)
                 |
        Input and Scope Resolver
                 |
      Durable Graph Orchestrator ---- Run State / Audit / Artifacts
                 |
       Repository Intelligence
                 |
 Taxonomy Registry / Capability Resolver
                 |
 Recommendation + explicit approval
                 |
 Neutral Test Planner -> Human plan approval
                 |
 Generation Service -> Adapter Registry
                 |
 Sandbox Controller -> App container + Test container (when needed)
                 |
 Quality & Evidence Engine -> bounded Repair proposal/retry
                 |
 Report Composer -> domain reports + consolidated report

Thin MCP / CI entrypoints invoke the same application service layer.
```

Workflow states: `NEW → INGESTED → ANALYZED → SCOPE_RESOLVED → RECOMMENDATIONS_PENDING (optional) → PLAN_DRAFTED → PLAN_APPROVED → GENERATED → EXECUTING → EVALUATED → (REPAIR_PENDING / REPAIR_APPROVAL / EXECUTING) → REPORTED`; terminal alternatives `REJECTED`, `CANCELLED`, `FAILED`, `PARTIAL`, `BLOCKED_ON_USER`.

Core component responsibilities: CLI/MCP/CI entrypoints; scope resolver; read-only repository intelligence; taxonomy/capability registry; durable workflow orchestrator; neutral planner; generation service; adapter registry; sandbox controller; quality/evidence engine; bounded repair controller; report composer; run/artifact store.

Repository analysis pipeline: enumerate with ignore/size limits; detect languages/frameworks/build/tests; parse with Tree-sitter/native parsers; extract symbols/signatures/imports/calls/routes; build dependency graph and RepoMap; discover tests/OpenAPI/GraphQL/schema/migrations/CI; map diffs to symbols/callers/tests; assemble evidence-bounded context. Static analysis must not import or execute project code.

### Data models / database schemas and API contracts (routes, payloads, auth)

No REST/HTTP API routes, endpoint paths, authentication scheme, database schema, or queue payload protocol were finalized or discussed. MCP is a planned thin interface; exact MCP tools/resources and auth were not defined. Do not invent endpoints or auth contracts.

Conceptual records (schemas still to define):

- **RunRequest:** project ref; repository revision/change base; scope selections/options/source; test-language preferences; target environment ref; approval/execution/quality policy refs; optional request text.
- **ResolvedScope:** taxonomy version; selected type records with support/prerequisites/adapter/options/reason; recommendations with state pending/approved/declined; conflicts, unresolved questions, hash.
- **TestScenario:** stable `scenario_id`; canonical `type_id`; domain tags; target symbol/endpoint/workflow/schema/requirement; evidence locations; intent; preconditions; deterministic data/fixtures; edge cases; expected outcomes/assertion intent; priority/risk; dependencies; provenance.
- **GeneratedArtifact:** scenario IDs, path, digest, adapter/version, patch provenance.
- **ExecutionEvidence:** normalized status; runner/environment digest; timestamps; command identity; stdout/stderr/artifact refs; coverage/mutation data; resource use; cleanup status.
- **DomainReport / RunReport:** domain/overall scope and status; plan/approval revisions; generated/reused tests; counts; duration; quality metrics; failure classes; repair diffs; evidence links; limitations; links to domain reports/raw evidence.

Per-run local output example:

```text
.testagent/
  runs/<run-id>/
    manifest.json
    scope.json
    plan/
    generated/
    evidence/<domain>/
    reports/<domain>.md
    reports/<domain>.json
    reports/consolidated.md
    reports/consolidated.json
```

Idempotency key concept: derived from run, stage, revision, and adapter invocation. Approval bound to run/scope/plan revision and hash. Run artifacts not committed by default; retention/deletion policy open.

### Third-party integrations and external dependencies

- **Tree-sitter** for multi-language parsing; AST/native parser options.
- **LangGraph** proposed for durable graph workflow/checkpoints/interrupts.
- **Docker / Docker Compose** proposed baseline for sandbox/sidecars; Docker SDK for Python appeared as a candidate.
- **Playwright** browser automation.
- **pytest, Vitest, JUnit 5, RestAssured, xUnit, Go test/Testify**, Robot Framework, Gherkin step runtimes, Karate as candidate adapters.
- **Coverage:** `coverage.py`, Istanbul, JaCoCo named as examples.
- **Mutation:** mutmut, Cosmic Ray, Stryker, PIT mentioned as examples; Mutahunter also appears in original project brief as a possible mutation testing tool. No exact selection settled.
- **Security:** Semgrep, Bandit, Trivy, OWASP ZAP candidates.
- **Performance:** k6 constrained templates/scripts, potentially derived from OpenAPI.
- **Fixtures/environment:** SQL scripts, Alembic, Testcontainers candidate approaches.
- **Isolation options later:** gVisor, Firecracker/MicroVM.
- **Potential semantic retrieval:** ChromaDB was mentioned as optional later; vector database not primary source of truth.
- **CI/CD and MCP:** accepted integration scope, specific provider and protocol surfaces not defined.

### Proposed repository structure

```text
autonomous-testing-agent/
├── pyproject.toml
├── README.md
├── PRD.md
├── TAD.md
├── .testagent.schema.json
├── config/{taxonomy/,profiles/,policies/}
├── docs/{decisions/,adapter-authoring.md,threat-model.md}
├── src/testagent/
│   ├── cli/ application/ domain/ workflow/ config/
│   ├── analysis/ planning/ generation/
│   ├── adapters/{base/,python_pytest/,javascript_vitest/,java_junit/,playwright/,tools/}
│   ├── execution/ quality/ repair/ reporting/ persistence/ mcp/ security/
├── sandbox/{images/,policies/}
├── schemas/{run-request.schema.json,plan.schema.json,result.schema.json,report.schema.json}
├── examples/{.testagent.yaml,sample-projects/}
└── tests/{contracts/,unit/,integration/,security/,acceptance/}
```

Proposal only; MVP need not implement every directory. Keep transport, domain logic, and adapters separable. Avoid adopting database/service topology before needs are measured.

## 5. Decision Log (Settled vs. Rejected)

### Confirmed Decisions

| Decision | Why / effect |
|---|---|
| Multi-select types/domains | Users may need unit + integration + API + regression, etc. |
| Additional recommendations require explicit approval | User controls test scope; recommendations do not authorize execution. |
| Individual domain reports and one consolidated report | Supports domain owners and unified release/quality view. |
| User chooses requested testing types | Product must not indiscriminately run all tests. |
| Accept all earlier proposed additional features | Change-aware analysis, impact analysis, traceability, deduplication, risk-based selection, historical failure learning, CI/CD, test maintenance are in product scope, phased. |
| Neutral plan before generation; approval gate | Make test intent and expected behavior reviewable before executable code. |
| Central orchestration + specialized profiles/adapters | Shared infrastructure and consistency; no need for 12 independent AI agents. |
| Separate source language and test language concepts | Enforce language boundary centrally before generation. |
| White-box unit language matches target source module | Unit tests rely on in-language build/runtime; exceptions require explicit supported binding. |
| Black-box API/E2E/performance may use another supported language | They target a running isolated application via interfaces. |
| Docker baseline with possible stronger isolation later | Practical initial isolation while recognizing Docker alone is not complete security boundary. |
| CI/MCP are interfaces, not separate engines | Avoid divergent behavior and policy bypass. |
| Bounded repair and human approval for sensitive changes | Prevent changes that merely turn failures green. |
| No implementation yet | Product/architecture documentation requested before coding. |

### Rejected Alternatives / explicitly ruled out

- **Single-select testing only:** rejected by final multi-select decision.
- **Agent autonomously choosing/running all possible test types:** rejected; user controls selection and additions need approval.
- **Run recommendations automatically:** rejected; require approval before execution.
- **One consolidated report only:** rejected; need per-domain reports plus consolidated report.
- **Treat REST/GraphQL, SAST/DAST, self-healing as equivalent “testing types”:** rejected conceptually; separate protocol/technique/capability dimensions while retaining user-facing labels.
- **12 independent AI agents for each domain:** recommendation explicitly rejected in favor of central orchestration and specialized profiles/adapters.
- **Vector database as primary code understanding/RAG:** rejected; structural AST/dependency graph/RepoMap is primary, semantic retrieval supplemental only.
- **Immediate generation without neutral plan and review:** rejected by plan-first approval workflow.
- **Executing generated commands/scripts directly on host or with arbitrary LLM shell strings:** rejected by sandbox and command policy.
- **Normal Docker treated as complete security guarantee:** explicitly rejected; stronger isolation considered for hosted/high-risk use.
- **Automatically rewriting failed assertions, adding skips, or changing app behavior to get green:** rejected without human approval; app business logic not auto-patched in MVP.
- **All languages/frameworks in first release:** rejected as impractical; adapter tiers and narrow vertical slice proposed.
- **Treating passing tests or coverage alone as evidence of usefulness:** rejected; assertion, mutation, repeatability, and other evidence needed.
- **Production execution inferred from a URL/config in repository:** rejected; explicit target authorization and restrictive policy required.
- **Unbounded retries/agent loops:** rejected in favor of 3–5 max bounded healing.

Not explicitly rejected/finalized: individual named frameworks/tools, database choice, queue, cloud/hosting, REST API routes/auth, exact coverage thresholds, provider/model, and numerical SLAs.

## 6. Open Questions & Immediate Next Steps

### Unresolved ambiguities and trade-offs

1. LLM provider/model, data handling, privacy, retention, and prompt/template version policy.
2. Local persistence format and retention/deletion guarantees; whether artifact store is sufficient or DB needed.
3. Hosted execution in initial release? If yes: tenant isolation and stronger sandbox decision (gVisor/Firecracker/etc.).
4. Exact Tier 1 adapter order and first supported source languages/frameworks based on target user repositories.
5. Which mutation tool(s) per language (mutmut, Cosmic Ray, Stryker, PIT, Mutahunter candidates) and how equivalent mutants are handled operationally.
6. Approval UX and trusted CI policy for non-interactive runs; exact scope of any break-glass mode.
7. Numerical quality thresholds (line/branch coverage, mutation score, flake repetitions) and whether advisory/blocking by profile. Example values 70% line, 60% branch were illustrative only.
8. Plugin/adapters trust model, signatures, distribution, pinning, compatibility/deprecation policy.
9. Supported OS/container runtimes; resource defaults and concurrency limits.
10. Exact REST/HTTP API surface, MCP tools/resources, auth model, and external CI provider integrations—none specified yet.
11. Target authorization process for DAST, penetration, load, deployment, fault injection, and any live environment.
12. Taxonomy versioning and final canonical IDs/profile design; diagrams are consolidated conceptually but registry schema is not yet created.
13. Whether test plan approval can be policy-preapproved in CI or always interactive; current default is required, configurable with explicit policy.
14. Specific acceptance criteria for product latency/throughput/availability; none were given.

### Exact task we were about to do next

The immediately preceding completed work was creation of **PRD.md** and **TAD.md** from the full project discussion and two uploaded testing-taxonomy PNGs. The current requested next task is to produce this single lossless context handoff file, `machine_a_project_context.md`. After this handoff, the next project decision/action should be to review and resolve the open choices above—especially MVP adapter order, execution/persistence deployment boundary, approval policy, and quality thresholds—before authorizing implementation. No code has been started.

