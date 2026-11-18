# ASTA Supporting Documentation Index

**Product:** Autonomous Software Testing Platform (ASTA)  
**Status:** Development reference set; implementation has not started.  
**Baseline documents:** [`PRD.md`](PRD.md), [`SRS.md`](SRS.md), [`TAD.md`](TAD.md)

This folder contains the approved product baseline and its supporting specifications. The supporting documents make the baseline traceable and actionable; they do not silently convert proposals or TBDs in the baseline into approved technology choices.

## Source-of-truth hierarchy

1. **PRD** defines product intent, personas, goals, scope, priorities, and user-facing policy.
2. **SRS** defines normative functional/non-functional requirements, states, verification statements, and TBDs. Its `shall` requirements remain the testable contract.
3. **TAD** defines the proposed logical architecture, boundaries, interactions, and technology candidates.
4. **Supporting specifications** below refine the above. Any conflict must be recorded and resolved; do not silently override the SRS.
5. **Architecture diagrams** are visual navigation aids; the textual TAD is authoritative where a diagram omits detail.

## Documents

| File | Purpose | Status |
|---|---|---|
| [`TRACEABILITY_MATRIX.md`](TRACEABILITY_MATRIX.md) | Links requirement IDs, product goals, design areas, and verification evidence. | Baseline trace; detailed implementation evidence is pending. |
| [`ADR_REGISTER.md`](ADR_REGISTER.md) | Records confirmed decisions, proposals, rejected constraints, and decisions still open. | Initial register; open items require owners and approval. |
| [`SECURITY_THREAT_MODEL.md`](SECURITY_THREAT_MODEL.md) | Assets, trust boundaries, threat scenarios, controls, and proof gates. | Design baseline; validation evidence is pending. |
| [`INTERFACE_AND_WORKFLOW_SPEC.md`](INTERFACE_AND_WORKFLOW_SPEC.md) | CLI/config/MCP workflows, approval semantics, and later API/UI contract candidates. | CLI workflow requirements are baseline; exact syntax and later contracts remain open. |
| [`TAXONOMY_AND_ADAPTER_MATRIX.md`](TAXONOMY_AND_ADAPTER_MATRIX.md) | Normalized testing catalogue, applicability, language boundaries, and adapter support status. | Taxonomy baseline; adapter/version support is provisional until verified. |
| [`DATA_AND_ARTIFACT_CONTRACTS.md`](DATA_AND_ARTIFACT_CONTRACTS.md) | Entity fields, invariants, lifecycle states, evidence, and report contract outline. | Logical contract; physical schema and retention details remain open. |
| [`VERIFICATION_AND_QUALITY_PLAN.md`](VERIFICATION_AND_QUALITY_PLAN.md) | Product quality gates, verification methods, benchmark fixtures, and release evidence. | Plan; numeric thresholds require approval. |
| [`FAILURE_RECOVERY_AND_STATE_MODEL.md`](FAILURE_RECOVERY_AND_STATE_MODEL.md) | Run/plan/attempt state transitions, failure outcomes, cancellation, and recovery. | Proposed operational contract derived from the SRS/TAD. |
| [`DEPLOYMENT_OPERATIONS_GUIDE.md`](DEPLOYMENT_OPERATIONS_GUIDE.md) | Local-first release/deployment assumptions, operations, diagnostics, and support constraints. | Deployment intent; OS, installer, paths, and service details remain open. |
| [`COMPATIBILITY_AND_DEPENDENCY_POLICY.md`](COMPATIBILITY_AND_DEPENDENCY_POLICY.md) | Adapter manifest requirements, dependency phases, licensing, and compatibility evidence. | Policy baseline; exact versions and licenses require verification. |
| [`RISKS_ASSUMPTIONS_OPEN_DECISIONS.md`](RISKS_ASSUMPTIONS_OPEN_DECISIONS.md) | Consolidated risk, assumption, and decision backlog with release impact. | Initial register; assign owners and review dates before implementation. |

## Change control

- Give new requirements stable IDs in the SRS before implementation; do not overload an existing ID.
- Update the traceability matrix when an SRS requirement, priority, phase, or acceptance condition changes.
- Record consequential architectural choices in the ADR register, including the chosen option, alternatives considered, rationale, owner, and date.
- If an approved change affects security, data, or user approval behavior, update the threat model and relevant contracts as part of the same change.
- Keep versioned run snapshots and immutable execution evidence compatible with the source specifications.
- Mark unknown values `TBD`; mark recommendations `Proposed`; reserve `Confirmed` for decisions actually agreed in the project discussion or baseline documents.

