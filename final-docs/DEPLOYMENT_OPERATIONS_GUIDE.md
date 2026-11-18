# ASTA Deployment and Operations Guide

**Status:** Deployment intent; packaging and operating-system decisions are open  
**Sources:** [`PRD.md`](PRD.md) §§1, 7; [`SRS.md`](SRS.md) §§3–4, 8, 11–13; [`TAD.md`](TAD.md) §§2–3, 8–9, 11–15

## 1. Deployment target and release shape

The confirmed product direction is a locally installed, local-first application with a CLI-first workflow and an optional MCP integration. M3 candidates add a REST API and React web UI using the same core services. This is not a decision that a Windows `.exe` is required. Supported operating systems, installer/packaging format, service/background-process model, and installation paths remain TBD.

Initial architecture assumes one worker per machine and bounded concurrency. Hosted, multi-worker, and multi-user deployment are later scope and must wait for isolation, persistence, authorization, and scale requirements.

## 2. Environment support declaration

Every release must publish verified combinations of:

- operating system and version;
- hardware/resource profile (including model/GPU needs if AI is enabled);
- container runtime and configuration, if applicable;
- supported project languages/frameworks and runtimes;
- adapter and external-tool versions;
- local model/provider configuration, if enabled;
- report formats and any feature marked partial/unsupported.

Do not advertise an OS or project type based solely on theoretical compatibility. TAD/SRS open item: prove Windows+WSL2/Docker or select Linux; initial proposal of Python web/API and plain websites is not approved support scope.

## 3. Installation and first-run operational requirements

Final installation steps depend on package format and OS decision. Any supported distribution must:

1. Verify runtime prerequisites before allowing code execution.
2. Explain whether isolation is available and the resulting mode. If the boundary is absent/unproven, disable untrusted execution and explain; optionally permit configured read-only analysis or trusted projects only.
3. Create data/artifact directories with user-only permissions where supported; exact paths and ACLs remain TBD.
4. Keep credentials in the selected OS keyring/encrypted secret store, outside ordinary config/DB records.
5. Make network behavior explicit: no execution egress by default; approved target and package registry access are separate policies.
6. Provide an AI-off path; local Ollama is proposed, not mandatory or selected. Remote providers are off unless explicitly opted in.
7. Display version, verified adapters/tools, config validation, and current security readiness before a run.

## 4. Runtime operating modes

| Mode | Allowed behavior | Conditions |
|---|---|---|
| Inspection/read-only | Deterministic static inspection/reporting of safe metadata; no module import or project code execution | Available even when execution sandbox is unavailable, subject to privacy/path policy. |
| Trusted-project execution | Execute selected checks only for projects trusted under a documented policy | Temporary fallback until sandbox/effectiveness proof passes; user must see trust mode. |
| Isolated execution | Approved checks through worker with source read-only, separate workspace, resource controls, network deny-by-default and teardown | Only on verified OS/runtime and after security proof gate. |
| AI-off | Rule-based inspection/planning, deterministic generators, execution/evaluation/reporting for supported paths | Must remain a complete supported path. |
| AI-enabled local | Model requests through gateway to configured local model | Model/version/license/resource profile verified; bounded schema and limits. |
| AI-enabled remote | Only explicitly enabled provider and data-sharing scope | Disclose/preview selected content; audit provider/model/task/choice/outcome. |

## 5. Configuration and policy operations

`.testagent.yaml` is the proposed project configuration contract. It may contain scope, enabled capabilities, options, language/framework hints, resource limits, retention, AI/data-sharing, and approvals where implemented. It cannot broaden runtime safety policy. Invalid config must fail before side effects with field-level explanation. Store a run snapshot so later edits do not rewrite past runs.

Do not place raw secrets in configuration or environment files. Refer to a credential store by scoped reference. Runtime changes to allowed targets, egress, adapter/tool version, or policy must be audited and invalidate affected approvals when material.

## 6. Local operations and observability

Required operating signals (from TAD):

- **Structured logs:** run ID, component ID, event/decision, duration, outcome; redact secrets and sensitive request content.
- **Audit events:** approvals, target decisions, AI data-sharing calls, egress decisions, cancellations, and artifact access.
- **Run diagnostics:** state, selected/blocked/unsupported checks, worker PID/health, adapter/tool version, limits, last safe checkpoint, report/artifact availability.
- **Health/readiness:** distinguish CLI/core, worker, adapters, model gateway, and persistence readiness. Missing optional AI should not make an AI-off core path unhealthy.
- **Timing:** measure planning, queue, execution, evaluation, report, and artifact phases separately.

Health endpoints, metrics export, log retention, log-file location, and telemetry consent are not selected. Avoid collecting project contents by default. No remote telemetry requirement is currently approved.

## 7. Backup, restore, upgrade, and deletion

The TAD proposes SQLite plus local content-addressed artifact files; backup/restore, transaction boundaries, data directory, schema migrations, and encryption are not selected. Before distributing a release:

- define an atomic/consistent backup procedure for DB plus referenced artifacts;
- test restore and verify artifact hashes and report/evidence references;
- define upgrade/migration rollback behavior and compatibility policy;
- define export/import format if project portability is required;
- enforce configured retention/deletion for project rows, artifacts, prompts/replies, scripts, reports, and backups;
- state what is deleted, retained for audit, or irrecoverable after deletion.

SQLAlchemy/Alembic is a candidate only; PostgreSQL/object storage are later possibilities if multi-user/hosted scale requires them. No database migration or storage choice is binding yet.

## 8. Incident and operational response

| Event | Immediate response | Preserve/record |
|---|---|---|
| Unauthorized network attempt | Block request, terminate affected check if necessary, keep deny-by-default, record target decision | Run/check IDs, canonical target, policy decision, request evidence with secrets redacted. |
| Sandbox escape/isolation failure suspected | Stop execution capability; terminate workers; mark affected run `Error`/`Blocked`; disable untrusted execution pending review | Worker/runtime version, host/platform, resource state, redacted logs, cleanup outcome. |
| Secret exposure suspected | Revoke/rotate scoped credential, stop affected run, restrict artifacts, follow approved deletion/incident process | Secret reference only, exposure locations, run IDs, provider disclosure where relevant. Never duplicate raw secret into incident notes. |
| Worker stuck/cancel fails | Terminate process group using supported host mechanism; remove network/mount/credential access; report cleanup failure | Process/resource IDs, timing, partial evidence, cleanup audit. |
| DB/artifact corruption | Stop positive result claims, mark evidence incomplete, preserve forensic copy if policy permits, restore from validated backup | Hash mismatch, affected runs/artifacts, recovery action. |
| Model/provider outage | Bounded retries then deterministic fallback/degraded state; continue AI-off path or stop affected optional step | Provider/model/task, data-sharing choice, error class and fallback. |

Detailed incident contacts/escalation and severity policy are not specified; define before a hosted or multi-user release.

## 9. Release operations checklist

- Publish package type and supported OS/runtime matrix; installation/uninstall/upgrade path verified.
- Verify worker isolation and egress on each supported environment.
- Run safe-only defaults; prove approval gates for all non-safe classes.
- Confirm AI-off full path and remote opt-in disclosure/audit if remote provider feature is shipped.
- Validate report schemas/formats, evidence redaction, and retention/deletion behavior.
- Attach adapter/tool/model license and version inventory.
- Provide backup/recovery and cancellation/cleanup diagnostics.
- Document known limitations, unsupported adapter cases, and no-certification wording.
- Approve numeric performance/concurrency thresholds and benchmark gates before production claims.

