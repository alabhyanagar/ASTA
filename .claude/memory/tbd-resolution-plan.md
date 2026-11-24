---
name: tbd-resolution-plan
description: Plan for resolving all 15 TBD items before M0 design freeze
metadata:
  type: project
---

# TBD Resolution Plan — ASTA Project

**Purpose**: Resolve all 15 TBD items listed in ASTA_M1_CLI_IMPLEMENTATION_BACKLOG.md Section 8 before transitioning to M0 design freeze.  
**Owner**: To be assigned during stakeholder review  
**Target Completion**: Before M0 entry  
**Priority**: All P0 items must have owners/estimates; P1 items should be addressed for M1 readiness

## TBD Items Categorization

### Category A: Critical for M0 Entry (Must resolve before M0)
| # | Item | Related Backlog Items | Action Required |
|---|------|----------------------|-----------------|
| 1 | Exact Python patch and dependency versions | ASTA-011, ASTA-060, ASTA-061, ASTA-062 | Pin versions; verify licenses; document supported OpenAPI versions |
| 2 | Exact WSL distribution/version policy and tested Windows editions/builds | ASTA-010, ASTA-011, ASTA-070 | Define supported WSL distros; test Windows editions; document ECI status |
| 3 | CLI command spellings and `asta.toml` schema | ASTA-020, ASTA-021, ASTA-022, ASTA-023 | Finalize command names; schema version; migration behavior |
| 4 | Numeric limits (CPU, memory, process, disk, output, timeout, API-rate) | ASTA-050, ASTA-051, ASTA-052, ASTA-053, ASTA-072 | Measure representative workloads; set approved defaults |
| 5 | Credential input UX (environment reference vs interactive prompt) | ASTA-053, NFR-SEC-005 | Design UX; decide on OS keyring integration for M1 |

### Category B: Important but Can Defer Slightly (Resolve in early M0)
| # | Item | Related Backlog Items | Action Required |
|---|------|----------------------|-----------------|
| 6 | SQLite physical schema/migrations, artifact hash algorithm/layout | ASTA-050, ASTA-051 | Design schema; choose hash algorithm; plan migration strategy |
| 7 | Report JSON fields, timestamp format, retention/deletion/backup | ASTA-090, ASTA-091, ASTA-092 | Define JSON schema; timestamp format; retention policy |
| 8 | Whether JUnit XML is included in M1 and JUnit outcome mapping | ASTA-093 | Validate mapping; decide inclusion; document CLI exit code policy |
| 9 | Whether archive intake is M1; exact expansion/path/file-size caps | ASTA-033, ASTA-050 | Prototype archive extraction; set caps; or defer to M2 |

### Category C: Strategic Decisions (Resolve with stakeholder input)
| # | Item | Related Backlog Items | Action Required |
|---|------|----------------------|-----------------|
| 10 | OpenAPI 3.0/3.1 support selection; Schemathesis enabled for M1 | ASTA-062, ASTA-071, ASTA-082 | Evaluate both; pick one for M1; document rationale |
| 11 | Security benchmark cases and minimum evidence for project-code execution | ASTA-074, NFR-SEC-001 | Define benchmark; set minimum evidence thresholds; document threat boundary |
| 12 | Exact release quality thresholds, bug-garden benchmark measures | ASTA-110, ASTA-111, ASTA-112 | Set severity scale; define bug-garden metrics; approve thresholds |
| 13 | Severity scale (Critical/High/Medium/Low/Informational) | NFR-SEC-001, ASTA-112 | Choose scale; document mapping to risk classes |
| 14 | Dependency vulnerability policy | NFR-MAINT-001, ASTA-112 | Review integrated tool licenses; define policy |
| 15 | Retention periods for artifacts, prompts, reports | NFR-PRIV-002, ASTA-113 | Define retention durations; encryption beyond disk encryption |

## Resolution Process

### Step 1: Owner Assignment
- Each TBD item needs an owner with authority to make decisions
- Owners must provide estimates and dependency reviews
- All P0 items must have owners before M0 can begin

### Step 2: Investigation & Evidence
- Owners investigate options and gather evidence
- For version/limit items: measure representative workloads
- For architecture items: prototype and test
- Document findings with pros/cons

### Step 3: Decision & ADR Recording
- Owners make decisions and record ADRs (Architecture Decision Records)
- ADRs must include: context, decision, consequences, alternatives considered
- ADRs link to corresponding backlog items and SRS requirements

### Step 4: Baseline Update
- Content baseline updated to new approved version
- All work items mapped to SRS requirements in traceability matrix
- M0 exit criteria met: Gate A and B pass

## Quick Wins (Can Resolve Fast)

### These may be resolved quickly with stakeholder alignment:
- **CLI command naming**: Can often be decided in a single session
- **Python version**: Typically aligned with what's available on target platforms
- **WSL support**: Usually one LTS version supported initially

### These require more investigation:
- **Numeric limits**: Need representative workload measurements
- **Schema designs**: Need input from multiple stakeholders
- **Security benchmarks**: Need threat modeling and test fixtures

---

*Plan created as part of project memory initialization. All 15 TBD items must be resolved with owners and evidence before M0 design freeze can begin.*