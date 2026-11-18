# ASTA Compatibility and Dependency Policy

**Status:** Policy baseline; exact stack/tool versions are unselected  
**Sources:** [`SRS.md`](SRS.md) §§4, 6, 8, 13, 15; [`TAD.md`](TAD.md) §§7, 13, 16  
**Related:** [`TAXONOMY_AND_ADAPTER_MATRIX.md`](TAXONOMY_AND_ADAPTER_MATRIX.md), [`ADR_REGISTER.md`](ADR_REGISTER.md)

## 1. Support claim rules

- Publish a verified OS/project-type/adapter support matrix for every release (`NFR-COMP-001`).
- Support is a tuple, not a broad language label: **OS/version × runtime × framework/project profile × adapter/tool version × mode**.
- Mark each combination `Supported`, `Partial`, `Unsupported`, or `Not verified`; never silently fall back to an unrelated tool or test language.
- Only adapters with manifest, applicability evidence, prerequisites, risk, limits, output mapping, supported OS/runtime, version, and license can execute.
- Tool/provider/model license review is required before distribution/hosting (`NFR-LIC-001`). Automated compliance checks must not be described as legal/regulatory certification (`NFR-COMP-002`).

## 2. Language and framework policy

The language-boundary rule is confirmed:

- White-box unit checks use the target module’s language and compatible runtime/build ecosystem unless an adapter explicitly declares supported binding.
- Black-box API/E2E/UI/performance checks may use another supported test language against an isolated running target.
- Component/integration scenarios declare white-box or black-box before language binding.
- No silent language substitution. Unsupported runtime/tool → `Unsupported`; missing resolvable prerequisite or policy → `Blocked`.

Initial target language/framework list is TBD. Python web/API and plain websites were a proposal only. The core technology proposal of Python modular monolith does not automatically imply all tested projects must be Python.

## 3. Dependency and adapter inventory requirements

Maintain a release inventory with at least:

| Field | Reason |
|---|---|
| Dependency/adapter ID and purpose | Identify application runtime vs. optional test tool. |
| Exact version and provenance | Reproduce reports and support update/rollback decisions. |
| License and redistribution terms | Required review before distribution/hosting. |
| Supported OS/runtime | Avoid unsupported execution claims. |
| Source and package integrity evidence | Record approved registry/artifact source; exact signing/SBOM policy is a pending decision. |
| Known vulnerabilities/review date | Release decision and mitigation tracking. |
| Adapter manifest/schema version | Ensure compatibility with the shared engine. |
| Commands, permissions, network needs | Prevent arbitrary commands and unintended egress. |
| Output schema/parser version | Preserve deterministic evidence mapping. |
| Limits and cleanup behavior | Enforce resource and security contracts. |

## 4. Candidate technologies recorded (not selected)

| Area | Candidate(s) | Status and required decision |
|---|---|---|
| Core | Python modular monolith | Recommended; validate packaging, target compatibility, and security. |
| CLI | Typer | Candidate; exact package/command name TBD. |
| Workflow | Persisted Python state machine; LangGraph if needs warrant | Recommendation, not selection. Define durability/idempotency first. |
| Persistence | SQLite; SQLAlchemy/Alembic optional | Proposed local baseline; migration/backup/concurrency decisions pending. |
| Artifact store | Local content-addressed files | Proposed; hash algorithm, path, deletion, backup TBD. |
| Secrets | OS keyring or selected encrypted store | Unselected; never store secret values in ordinary records. |
| Worker/sandbox | One worker per machine; Docker/rootless where supported | Proposed; must pass proof; Docker alone is not a hostile-code guarantee. |
| AI | Ollama local-first; remote OpenAI-compatible provider optional/off by default | Proposed; choose model/provider only after quality, hardware, privacy, and license review. |
| REST API | FastAPI + Pydantic | M3 candidate; auth/network/error contract unselected. |
| Web UI | React + TypeScript + Vite | M3 candidate; same core services. |
| Reports | Markdown + versioned JSON; later HTML/JUnit XML/SARIF | M1/M3 candidates; only offer validated formats. |
| Testing tools | Playwright, axe-core, Schemathesis, pytest/HTTPX, Semgrep, Bandit, Gitleaks, pip-audit, OSV-Scanner, OWASP ZAP, Locust | Candidates; exact versions, licenses, commands, platform, and output parsers unverified. |

## 5. Dependency installation and execution boundary

- Treat project dependencies, package installation hooks, compiler/build scripts, test scripts, and tool output as untrusted.
- Separate dependency installation from test execution. Installation phase may reach only approved package sources/registries and runs under isolation/resource limits.
- Execution phase has no network except approved target paths through the egress controller.
- Record lockfiles/resolved versions, tool versions, and environment identity in run evidence.
- Do not pass host-wide credentials or environment variables into adapters. Use scoped, short-lived references.
- Exact registry allowlist, cache behavior, package signing verification, SBOM format, and vulnerability response SLA remain open decisions.

## 6. Versioning and compatibility policy to approve

Before the first stable release, select:

1. Product SemVer policy and whether pre-1.0 breaking changes are allowed.
2. Adapter manifest contract version and compatibility rules between core and adapter.
3. Report JSON `schema_version` and migration/backward-compatibility window.
4. `.testagent.yaml` schema versioning and unknown-key behavior.
5. Supported Python/runtime/OS versions and deprecation window.
6. Tool update cadence, security patch response, pinning, and rollback policy.
7. SBOM generation, package-source provenance/signature verification, vulnerability triage, and license approval process.
8. Whether optional adapters are bundled, downloaded on demand, or invoked from user-installed tools; each changes license, update, and sandbox obligations.

## 7. Release compatibility evidence

For each declared combination, retain a passing representative project fixture, negative/unsupported fixture, resource and security evidence, adapter output parser result, license review, and known limitation. If any evidence is missing, mark the combination `Not verified` or `Partial`; do not infer support from a successful compile or tool installation.

