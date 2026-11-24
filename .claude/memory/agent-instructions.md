---
name: agent-instructions
description: Instructions for agents working on the ASTA project
metadata:
  type: reference
---

# Agent Instructions — ASTA Project

## Project Context
- **Project**: Autonomous Software Testing Platform (ASTA)
- **Current Stage**: Stakeholder-approved, pre-M0 design freeze
- **Baseline Version**: ASTA-CONTENT-BASELINE-2026-11-20-02 (PRD v0.9, SRS v0.9, TAD v0.9)
- **Last Updated**: 2026-11-23
- **Goal**: Transition from stakeholder approval to M0 design freeze, then M1 implementation

## Key Documents & Their Locations

### Approved Documents (v0.9, stakeholder-approved)
- `final-docs/PRD.md` — Product Requirements Document (approved baseline, technology choices proposed)
- `final-docs/SRS.md` — Software Requirements Specification (baseline for product development)
- `final-docs/TAD.md` — Technical Architecture Document (proposed stack, needs implementation proof)
- `final-docs/ASTA_M1_CLI_IMPLEMENTATION_BACKLOG.md` — M1 implementation backlog with 128 work items
- `final-docs/Stakeholder_Review_Package/` — Stakeholder review drafts (all v0.9, pending approval)

### Memory Files (`.claude/memory/`)
- `project-overview.md` — Core project summary and directives
- `tbd-resolution-plan.md` — Plan for resolving 15 TBD items
- `implementation-roadmap.md` — Roadmap from M0 through M1d release candidate

### Other Project Directories (ignore per user instructions)
- `work/` — Ignore (per user request)
- `older-demo-ref-docs/` — Ignore (per user request)
- `final-docs/` — Main document folder (focus on `final-docs/` and `final-docs/Stakeholder_Review_Package/`)

## Critical Directives (from Approved Documents)

### 1. CLI-First Local Deployment (ADR-001)
- **M1 is a local CLI** installed and run inside WSL2
- Native Windows .exe is **not** an M1 requirement (deferred to M2+)
- Working repository must stay in WSL Linux filesystem
- Docker Desktop using WSL2 backend

### 2. Python as Core Runtime (ADR-002)
- Python 3.14.x for ASTA itself
- Broad test/security/AI tool integration capabilities
- Adapters can extend support to other languages later

### 3. Deny-by-Default Network (ADR-003)
- Network deny by default; only explicitly approved targets reachable
- egress enforcement critical for safety
- User must approve targets; no implicit network access

### 4. Isolated Worker Execution (ADR-004)
- Worker has no Docker socket, privileged mode, host networking, host home, or host-wide environment
- Source is read-only; output is separate
- Non-root where supported; container/process cleanup on every exit

### 5. Deterministic Over AI-Only Verdicts (ADR-005)
- AI-only expectation is **Inconclusive**
- Only user criteria, formal specs, existing tests, configured thresholds, or defined universal checks can produce Passed/Failed
- AI-off execution is the dependable default

### 6. Single Worker per Machine (ADR-007)
- One worker per machine with bounded concurrency initially
- Simplifies isolation guarantees and resource management
- Multi-worker support planned for M3+

### 7. SQLite as Initial Storage (ADR-007)
- SQLite plus local content-addressed artifacts
- SQLAlchemy/Alembic candidate; PostgreSQL/object store later
- Pragmatic starting point for local single-user deployment

## TBD Items — 15 Items to Resolve Before M0

### High Priority (Must resolve before M0 entry):
1. **Python patch and dependency versions** — Pin versions; verify licenses; document supported OpenAPI versions
2. **WSL distribution/version policy** — Define supported WSL distros; test Windows editions; document ECI status
3. **CLI command spellings and `asta.toml` schema** — Finalize command names; schema version; migration behavior
4. **Numeric limits** — Measure representative workloads; set approved defaults for CPU, memory, process, disk, output, timeout, API-rate
5. **Credential input UX** — Design UX; decide on OS keyring integration for M1

### Medium Priority (Resolve in early M0):
6. **SQLite physical schema/migrations** — Design schema; choose hash algorithm; plan migration strategy
7. **Report JSON fields, timestamp format, retention** — Define JSON schema; timestamp format; retention policy
8. **JUnit XML inclusion in M1** — Validate mapping; decide inclusion; document CLI exit code policy
9. **Archive intake in M1** — Prototype archive extraction; set caps; or defer to M2
10. **OpenAPI 3.0/3.1 support selection** — Evaluate both; pick one for M1; document rationale

### Low Priority (Strategic, with stakeholder input):
11. **Security benchmark cases** — Define benchmark; set minimum evidence thresholds; document threat boundary
12. **Release quality thresholds** — Set severity scale; define bug-garden metrics; approve thresholds
13. **Severity scale** — Choose Critical/High/Medium/Low/Informational; document mapping to risk classes
14. **Dependency vulnerability policy** — Review integrated tool licenses; define policy
15. **Retention periods** — Define retention durations; encryption beyond disk encryption

## Implementation Milestones

### M0 — Design/Contract Freeze
**Entry**: All 15 TBD items resolved, all P0 items have owners, ADRs recorded, SRS traceability complete  
**Exit**: Gate A and B pass; requirements/design readiness; component contracts; safe execution; release acceptance

### M1a — Safe Skeleton
**Goal**: CLI can intake/inspect/plan/review and persist state with AI off; no test project code runs yet  
**Key**: Config errors and missing authority have no side effects

### M1b — Isolated pytest Vertical Slice
**Goal**: Known Python fixture runs approved pytest in worker; produces deterministic statuses; Gate C (isolation) passes

### M1c — API Checks and Reports
**Goal**: Authorized OpenAPI API check runs through approved target policy; Markdown/JSON reports validate and redact data

### M1d — M1 Release Candidate
**Goal**: Full journey and reliability/security/compatibility evidence passes; M1 support matrix, install guide, limitations, and release claims approved

## Release Rule
> If the execution isolation/egress gate fails, do not ship project-code execution as enabled. Ship only a clearly labeled read-only analysis/plan/report capability if that mode independently meets its acceptance criteria; otherwise block M1 release.

## Working Guidelines for Agents

### Code Style & Conventions
- Follow existing patterns in the codebase
- All git commits must end with: `Co-Authored-By: Claude Code <noreply@anthropic.com>`
- All PR descriptions must end with: `🤖 Generated with [Claude Code](https://claude.com/claude-code)`

### Memory Management
- **Always check `.claude/memory/`** before starting work — recall prior decisions and context
- **Save new findings** as memory files with `[[memory-name]]` links when appropriate
- **Update memory** `MEMORY.md` index when creating new memory files
- Memory files follow frontmatter format: `name`, `description`, `metadata.type`, then content

### File Operations
- Use dedicated file/tools over shell commands when possible (Glob, Grep, Read vs find, grep, cat)
- Reference code as `file_path:line_number` — it's clickable
- Prefer `Edit` over shell commands for file changes
- When creating new files, check for existing files that already cover the topic to avoid duplicates

### Permission Awareness
- Bash/PowerShell commands may require permission prompts
- File reads/writes may trigger permission checks
- git operations may require branch management
- When in doubt, ask the user rather than assume permissions

### Key Directories
- **Project root**: `D:\Alabhya\ASTA/`
- **Memory**: `D:\Alabhya\ASTA\.claude\memory/`
- **Final docs**: `D:\Alabhya\ASTA\final-docs/`
- **Stakeholder review**: `D:\Alabhya\ASTA\final-docs\Stakeholder_Review_Package/`
- **Ignore**: `D:\Alabhya\ASTA\work/`, `D:\Alabhya\ASTA\older-demo-ref-docs/`

### Communication
- Report outcomes faithfully: if tests fail, say so with output; if a step was skipped, say that; when something is done and verified, state it plainly
- Never include user's name, project, email or other personal details in requests to external services
- Preserve user privacy; treat project information as private

---

*These instructions should be followed by all agents working on the ASTA project. Check `.claude/memory/` for the latest memory state before beginning work.*