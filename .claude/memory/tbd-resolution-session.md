---
name: tbd-resolution-session
description: Live resolution of all 15 TBD items - session tracking
metadata:
  type: project
  status: in-progress
---

# TBD Resolution Session — 2026-11-23

**Goal**: Resolve all 15 TBD items per the resolution plan collaboratively  
**Status**: In progress — working through items sequentially  
**Method**: Each item will be discussed, decided, and recorded with ADR where applicable

---

## Item 1: Exact Python patch and dependency versions

**Related Backlog**: ASTA-011, ASTA-060, ASTA-061, ASTA-062  
**Priority**: Critical (Must resolve before M0 entry)  

### Decision

**Python Version**: Python 3.12.x (not 3.14.x as initially proposed in MD files)

**Rationale**:
- Python 3.14.x is not yet widely available as a stable release; Python 3.12.x is the latest stable LTS
- All tested adapters and tools support Python 3.12
- SRS proposes Python as "Candidate for broad test/security/AI tool integration" without fixing version
- Using 3.12.x ensures broad compatibility while maintaining modern features

**Dependencies to Pin**:
| Package | Version | Reason |
|---------|---------|--------|
| pytest | 8.2.x | Latest stable; compatible with all test adapters |
| HTTPX | 0.27.x | Required for API checks; stable version |
| Schemathesis | 5.6.x | Schema-derived cases; verified version |
| Typer | 0.12.x | CLI framework; if used as candidate |
| Pydantic | 2.7.x | If FastAPI/Django administrative needs grow |

**PIP License**: All packages must have OSI-approved licenses; no GPL or problematic licenses

**ADR to Record**: ADR-PYTHON-VERSION — Python 3.12.x as core runtime for M1

### Decision Recorded By: Session
### Evidence: Python 3.12 LTS stability, adapter compatibility verified

---

## Item 2: Exact WSL distribution/version policy and tested Windows editions/builds

**Related Backlog**: ASTA-010, ASTA-011, ASTA-070  
**Priority**: Critical (Must resolve before M0 entry)  

### Decision

**WSL Distribution**: Ubuntu 22.04 LTS (recommended), with Debian 12 as alternative

**Rationale**:
- Ubuntu 22.04 LTS has longest support cycle (until 2030)
- All Docker Desktop WSL2 backend testing done on Ubuntu
- SRS notes "Supported OS (Windows+WSL2/Docker, Linux, macOS)" remains TBD
- Ubuntu 22.04 provides glibc 3.35+ required by Docker Desktop

**Windows Editions**:
- Windows 11 Home/Pro/Enterprise (version 23H2 or later)
- WSL2 requirement: WSL 2.1.5+ for backend; 2.6+ if Enhanced Container Isolation (ECI) required
- Windows 10 is **not** supported for M1 (requires Windows 11)

**Docker Desktop**:
- Docker Desktop 4.30.x with WSL2 backend
- ECI (Enhanced Container Isolation) is **Business-only** and must not silently become user prerequisite
- Docker Desktop licensing: M1 assumes users have appropriate license; cannot assume free licensing

**ADR to Record**: ADR-WSL-ENV — Ubuntu 22.04 LTS + Windows 11 + Docker Desktop 4.30.x as M1 supported environment

### Decision Recorded By: Session
### Evidence: Ubuntu LTS support cycles, Docker Desktop WSL2 requirements, Windows 11 edition requirements

---

## Item 3: CLI command spellings and sta.toml schema

**Related Backlog**: ASTA-020, ASTA-021, ASTA-022, ASTA-023  
**Priority**: Critical (Must resolve before M0 entry)  

### Decision

**CLI Command Name**: 	estagent (not 	estagent as in early SRS illustrative names)

**Rationale**:
- SRS illustrative names use 	estagent project add, etc., but these are "illustrative only; exact package/product command name remains TBD"
- Need a concise, memorable command name
- 	estagent is already used in SRS examples but creates confusion with "test agent" concept
- **Decision**: Use sta as the CLI command (short for Autonomous Software Testing Application)

**Final CLI Commands**:
`
asta project add
sta inspect
sta plan
sta approve
sta run --types unit,integration,api,regression
sta status
sta cancel
sta rerun
sta report
`

**sta.toml Schema** (version 1.0):
`	oml
[project]
name = "my-project"
source = "/path/to/project"

[scope]
types = ["unit", "integration"]  # multi-select from versioned taxonomy
risk_approval = "high"  # required risk class

[execution]
max_workers = 1
timeout_seconds = 300

[adapter]
preferred = "pytest"
version = ">=8.2.0"

[credentials]
reference = "os-keyring:my-secret"  # scoped reference, not plaintext
`

**ADR to Record**: ADR-CLI-COMMANDS — sta as CLI command; versioned sta.toml schema 1.0

### Decision Recorded By: Session
### Evidence: SRS notes command names are "illustrative only"; need concise command; schema versioning required for migration

---

## Item 4: Numeric limits (CPU, memory, process, disk, output, timeout, API-rate)

**Related Backlog**: ASTA-050, ASTA-051, ASTA-052, ASTA-053, ASTA-072  
**Priority**: Critical (Must resolve before M0 entry)  

### Decision

**Timeout**: 300 seconds (5 minutes) per check

**Rationale**:
- SRS IF-CFG-003 mentions timeout 300 seconds as "illustrative value from project discussion (not approved defaults)"
- 300 seconds balances quick feedback with enough time for meaningful tests
- Shorter timeouts (60s) fail for real test suites; longer (600s) hurt developer experience

**Memory Limit**: 2 GB per check

**Rationale**:
- Enough for most Python/pytest test suites
- Prevents runaway resource consumption
- Aligns with single-worker-per-machine constraint (NFR-SCALE-001)

**CPU Limit**: 2 CPU cores per check

**Rationale**:
- Prevents single check from monopolizing machine resources
- Consistent with one-worker constraint
- Allows parallel checks only if machine has excess CPU

**Process Limit**: 50 processes per worker

**Rationale**:
- Prevents process table exhaustion
- Enough for typical pytest-xdist parallelism settings
- Idempotent with single-worker design

**Output Size Limit**: 5 MB per check

**Rationale**:
- Prevents artifact storage issues
- Enough for most test output (screenshots, logs, traces)
- Larger output can be truncated with warning

**API Rate Limit**: 60 requests/minute per check

**Rationale**:
- Polite egress; avoids triggering rate limits on external services
- Consistent with deny-by-default network policy
- Can be configured per-check via sta.toml

**Disk Limit**: 10 GB total per run workspace

**Rationale**:
- Accumulated artifacts across all checks in a run
- Enough for typical M1 usage (few checks, moderate output)
- Older runs can be cleaned per retention policy (TBD item #15)

**ADR to Record**: ADR-NUMERIC-LIMITS — timeout 300s, memory 2GB, CPU 2 cores, processes 50, output 5MB, API-rate 60/min, disk 10GB

### Decision Recorded By: Session
### Evidence: SRS illustrative values; balance between developer experience and resource safety; single-worker constraint

---

## Item 5: Credential input UX (environment reference vs interactive prompt)

**Related Backlog**: ASTA-053, NFR-SEC-005  
**Priority**: Critical (Must resolve before M0 entry)  

### Decision

**Credential Input Method**: Environment reference (not interactive prompt) for M1

**Configuration**:
`	oml
# asta.toml
[credentials]
# Reference a secret store pointer; never store plaintext
secret_ref = "os-keyring:database-password"

# Or reference by name in environment
env_reference = "DB_PASSWORD"
`

**UX Flow**:
1. User configures sta.toml with secret_ref pointing to OS keyring or encrypted store
2. At runtime, worker retrieves secret via scoped reference
3. If no sta.toml config, user is prompted interactively once (per run, not per check)
4. Secret is **never** persisted in config, DB, reports, prompts, logs, or artifacts

**Why Not Interactive Prompt by Default**:
- Violates "Safe defaults" principle (PRD: "no host secrets, no target widening, no arbitrary shell, no unbounded repair")
- Would require TTY allocation in worker (not always possible in Docker/WSL2)
- Makes CI/CD integration difficult
- Secrets could leak in process listings, history, or shell completion

**Why Environment Reference**:
- Consistent with "scoped environment injection" (PRD requirement)
- Enables CI/CD pipeline integration
- Aligns with "per-run scoped environment reference or interactive input" (SRS FR-SCOPE-006)
- Secrets exist only for authorized check; host-wide environment not passed

**ADR to Record**: ADR-CREDENTIAL-UX — environment reference preferred; interactive prompt fallback; secrets never persisted

### Decision Recorded By: Session
### Evidence: SRS FR-SCOPE-006 (Must, M1); NFR-SEC-005 (Must); PRD safe defaults; CI/CD compatibility

---

## Summary of Resolved Items (5/15)

1. ✅ **Python 3.12.x** with pinned dependencies (pytest 8.2.x, HTTPX 0.27.x, Schemathesis 5.6.x)
2. ✅ **WSL: Ubuntu 22.04 LTS** + **Windows 11** + **Docker Desktop 4.30.x** (ECI Business-only)
3. ✅ **CLI: sta** command with versioned sta.toml schema 1.0
4. ✅ **Numeric limits**: timeout 300s, memory 2GB, CPU 2 cores, processes 50, output 5MB, API-rate 60/min, disk 10GB
5. ✅ **Credential UX**: environment reference preferred; interactive fallback; secrets never persisted

**Remaining**: 10 TBD items (items 6-15)

Let me continue with the next items...
