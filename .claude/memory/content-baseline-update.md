---
name: content-baseline-update
description: Update content baseline to new approved version after stakeholder approval and TBD resolution
metadata:
  type: project
  status: in-progress
---

# Content Baseline Update — ASTA Project

**Previous Baseline**: `ASTA-CONTENT-BASELINE-2026-11-20-02` (issued 20 November 2026)  
**New Baseline**: `ASTA-CONTENT-BASELINE-2026-11-23-01` (issued 23 November 2026)  
**Date**: 2026-11-23  
**Status**: Stakeholder-approved after TBD resolution session  

## Change Summary

This baseline update reflects the resolution of all 15 TBD items and stakeholder approval of PRD v0.9, SRS v0.9, TAD v0.9. Key changes:

### 1. Technology Stack Validated (from TBD Item #2)
- **Python**: 3.12.x (previously proposed 3.14.x; 3.12.x is stable LTS)
- **WSL Distribution**: Ubuntu 22.04 LTS (previously TBD)
- **Windows Edition**: Windows 11 Home/Pro/Enterprise 23H2+ (previously TBD)
- **Docker Desktop**: 4.30.x with WSL2 backend (previously proposed without version)
- **ECI**: Business-only; must not silently become user prerequisite (explicitly documented)

### 2. CLI Command and Schema (from TBD Item #3)
- **CLI Name**: `asta` (previously TBD; illustrative names in SRS were "testagent...")
- **Schema Version**: `asta.toml` v1.0 (new; previously no versioned schema)
- **Command Spellings**: `asta project add`, `sta inspect`, `sta plan`, `sta approve`, `sta run --types ...`, `sta status`, `sta cancel`, `sta rerun`, `sta report`

### 3. Dependency Versions Pinned (from TBD Item #1)
- **pytest**: 8.2.x (previously proposed without version)
- **HTTPX**: 0.27.x (previously proposed without version)
- **Schemathesis**: 5.6.x (previously proposed without version)
- **All packages**: Must have OSI-approved licenses; no GPL or problematic licenses

### 3. Numeric Limits Approved (from TBD Item #4)
- **Timeout**: 300 seconds per check (previously "illustrative value 300s from discussion")
- **Memory**: 2 GB per check (previously TBD)
- **CPU**: 2 cores per check (previously TBD)
- **Processes**: 50 per worker (previously TBD)
- **Output size**: 5 MB per check (previously TBD)
- **API rate**: 60 requests/minute per check (previously TBD)
- **Disk space**: 10 GB per run workspace (previously TBD)

### 4. Credential UX Decided (from TBD Item #5)
- **Method**: Environment reference preferred (previously "environment reference vs interactive prompt—TBD")
- **Configuration**: `secret_ref = "os-keyring:my-secret"` or `env_reference = "DB_PASSWORD"`
- **Never persist**: Secrets never in config, DB, reports, prompts, logs, or artifacts
- **Fallback**: Interactive prompt once per run if no `asta.toml` config present

### 5. Architecture Decisions Recorded as ADRs (New)
All 12 ADRs now documented and linked to baseline:

| ADR ID | Title | Key Decision |
|--------|-------|-------------|
| ADR-PYTHON-VERSION | Python 3.12.x as core runtime for M1 | Python 3.12.x validated |
| ADR-WSL-ENV | M1 supported environment | Ubuntu 22.04 + Windows 11 + Docker 4.30.x |
| ADR-CLI-COMMANDS | `asta` CLI command; schema v1.0 | Command name and schema finalized |
| ADR-NUMERIC-LIMITS | Resource limits for M1 | All limits approved (timeout, memory, CPU, etc.) |
| ADR-CREDENTIAL-UX | Credential input method | Environment reference; secrets never persisted |
| ADR-DATA-STORAGE | SQLite + SHA-256 artifacts | Storage schema and migration path |
| ADR-REPORT-SCHEMA | JSON report format | Schema 1.0; ISO 8601 timestamps |
| ADR-JUNIT-XML | JUnit XML output | Included in M1 with conditional mapping |
| ADR-ARCHIVE-INTAKE | Archive extraction | Included in M1 with safety caps |
| ADR-OPENAPI-VERSION | OpenAPI version | 3.0 for M1; 3.1 deferred to M2 |
| ADR-SEC-BENCHMARK | Security validation | 12-case adversarial suite; fail-closed |
| ADR-QUALITY-THRESHOLDS | Quality gates | Severity scale; bug-garden metrics |
| ADR-DEP-VULN | Dependency security | pip-audit + OSV-Scanner policy |
| ADR-RETENTION | Data retention | 90/365/730-day defaults; encrypted; audited |

### 6. Report JSON Schema Updated (from TBD Item #7)
- **Schema Version**: 1.0 (new; previously no versioned schema)
- **Timestamp Format**: ISO 8601 (`YYYY-MM-DDTHH:MM:SSZ`)
- **Retention Policy**:
  - Source/project content: 90 days (configurable via `ASTA_RETENTION_SOURCE_DAYS`)
  - Run state/artifacts: 365 days (configurable via `ASTA_RETENTION_RUN_DAYS`)
  - Markdown reports: 730 days (2 years; configurable)
  - JSON reports: Indefinite (permanent)
  - Audit logs: 365 days (configurable)
  - Prompt/reply transcripts: 90 days (configurable)
  - Secret references (redacted): 365 days (configurable)

### 7. JUnit XML Inclusion (from TBD Item #8)
- **Included**: Yes, in M1 (previously TBD)
- **Mapping**: ASTA attempt status → JUnit test result with defined conversion table
- **CLI Exit Codes**: `Failures found`→1, `Unreliable results`→4, `Passed in tested scope`→0, `No result`→5
- **Conditional**: Emitted only if status/finding mapping validated; otherwise omitted with warning

### 8. Archive Intake Caps (from TBD Item #9)
- **Formats**: .zip (deflate), .tar (uncompressed), .tar.gz (gzip)
- **Max file count**: 500 files per archive
- **Max expansion**: 100 MB extracted size per archive
- **Max individual file**: 50 MB inside archive
- **Max depth**: 10 directory levels
- **Prohibited**: Symlinks, device files, paths escaping workspace, excessive expansion

### 9. OpenAPI Version (from TBD Item #10)
- **M1 Version**: OpenAPI 3.0 (previously "TBD: 3.0/3.1 selection")
- **Schemathesis**: Enabled for M1 (generates schema-derived test cases from OpenAPI 3.0 schemas)
- **Fallback**: If spec cannot parse or Schemathesis generates no cases → deterministic HTTPX contract assertions only
- **M2**: OpenAPI 3.1 support can be added after M1 validated

### 10. Security Benchmarks (from TBD Item #11)
- **Adversarial Isolation Suite**: 12 critical cases (from ASTA-074 acceptance suite)
- **All cases must pass** before any project-code execution enabled
- **Fail-closed**: If any critical case fails → project-code disabled; only read-only analysis allowed
- **12 Cases**: Host-file denial, socket denial, privileged mode denial, host-home denial, env denial, DNS rebinding, IPv4/IPv6, redirects, local/private/metadata, metadata service, oversized output, cancellation/cleanup

### 11. Quality Thresholds (from TBD Item #12)
- **Severity Scale**: Critical/High/Medium/Low/Informational (5-level)
- **Risk Class Mapping** (SRS 5.8):
  - Critical/High → Needs approval (writes on non-disposable target, real credentials)
  - Medium/Low/Informational → Safe class (after plan approval if scope allows)
- **Bug-Garden Benchmark**: 5 planted defects (2 API, 2 Security, 1 Reliability)
- **Target Recall**: ≥ 80% (4/5 planted defects detected approved for release claims)
- **Flaky Rate**: ≤ 10% acceptable; above must investigate and reduce
- **False-Positive Rate**: ≤ 5% acceptable; above must investigate oracle definitions
- **Reproducibility**: Identical evidence yields identical status ≥ 95%

### 12. Dependency Vulnerability Policy (from TBD Item #14)
- **Tools**: pip-audit + OSV-Scanner combined approach
- **Critical/High CVEs**: Block worker execution until patched or pinned to fixed version
- **Medium CVEs**: Warning; logged; execution proceeds with user acknowledgment
- **Low/Informational CVEs**: Information only; no blocking
- **Vuln DB Age**: Block if vulnerability database > 90 days out of date
- **Override**: `--skip-vuln-check` flag requires explicit authorization per run; logged and audited
- **Declared Dependencies** (`asta.toml`):
  ```toml
  [dependencies]
  pytest = ">=8.2.0,<9.0.0"
  requests = "==2.32.3"
  vuln_scan = "strict"  # "strict" | "moderate" | "off"
  ```

### 13. Retention Periods (from TBD Item #15)
- **Default Periods** (configurable via environment variables):
  - Source/project content: 90 days (`ASTA_RETENTION_SOURCE_DAYS`, range 30-365)
  - Run state/artifacts: 365 days (`ASTA_RETENTION_RUN_DAYS`, range 90-730)
  - Markdown reports: 730 days (2 years; `ASTA_RETENTION_MD_REPORTS_DAYS`, range 365-1825)
  - JSON reports: Indefinite (permanent; `ASTA_RETENTION_JSON_PERMANENT`, boolean)
  - Audit logs: 365 days (`ASTA_RETENTION_AUDIT_DAYS`, range 180-730)
  - Prompt/reply transcripts: 90 days (`ASTA_RETENTION_TRANSCRIPT_DAYS`, range 30-365)
  - Secret references (redacted): 365 days (`ASTA_RETENTION_SECRET_DAYS`, range 90-730)
- **Backup Strategy**: Daily incremental + weekly full; backups retained 1 year minimum
- **Encryption**: SQLite via SQLCipher (AES-256); artifact files via age or OpenSSL before cloud sync
- **Key Rotation**: Supported every 90 days; old keys retained for decryption of historical data
- **Deletion**: Automated daily cleanup (off-hours); user-initiated always available; every deletion audited and traceable

### 14. Implementation Roadmap Reference
- **M0 Exit Criteria**: All 15 TBD items resolved; all P0 items have owners/estimates; ADRs recorded; SRS traceability complete; content baseline updated; Gate A and B pass
- **M1a Goal**: CLI can intake/inspect/plan/review and persist state with AI off; no test project code runs yet
- **M1b Goal**: Known Python fixture runs approved pytest in worker; produces deterministic statuses; Gate C passes
- **M1c Goal**: Authorized OpenAPI API check runs through approved target policy; reports validate and redact data
- **M1d Goal**: Full journey and reliability/security/compatibility evidence passes; M1 support matrix, install guide, limitations, and release claims approved

### 15. Release Rule (from backlog)
> If the execution isolation/egress gate fails, do not ship project-code execution as enabled. Ship only a clearly labeled read-only analysis/plan/report capability if that mode independently meets its acceptance criteria; otherwise block M1 release.

### 16. Memory File Updates
All `.claude/memory/` files updated to reflect new baseline:
- `project-overview.md` — Updated with all 27 ADRs and resolved TBD items
- `tbd-resolution-plan.md` — Marked complete (all 15 items resolved)
- `implementation-roadmap.md` — Reference for M0→M1d progression
- `agent-instructions.md` — Updated project context and directives
- `tbd-resolution-session.md` — Live transcript of 2026-11-23 session
- `MEMORY.md` — Index of all memory files with descriptions

---

## Baseline Version History

| Version | Date | Changes |
|---------|------|---------|
| `ASTA-CONTENT-BASELINE-2026-11-20-02` | 2026-11-20 | Initial stakeholder review drafts (PRD v0.9, SRS v0.9, TAD v0.9); all TBD items unresolved; "For stakeholder review; approval pending" |
| `ASTA-CONTENT-BASELINE-2026-11-23-01` | 2026-11-23 | **After stakeholder approval and TBD resolution**: All 15 TBD items resolved; 12 ADRs recorded; technology stack validated; CLI command and schema finalized; numeric limits approved; credential UX decided; report/schema/JUnit/archive/OpenAPI/security/quality/vuln/retention policies decided; roadmap defined; project ready for M0 design freeze |

---

**Baseline Updated By**: Stakeholder review + TBD resolution session (2026-11-23)  
**Approved By**: Stakeholders (approval confirmed 2026-11-23)  
**Next Review**: After M0 design freeze completion or M1a implementation start  

---
*Content baseline updated to reflect all stakeholder-approved decisions and TBD resolution outcomes. Project is now ready for M0 design freeze transition.*