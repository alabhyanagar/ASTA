#!/usr/bin/env python3
"""
ASTA M1 Deterministic Planner

Creates testing plans from project evidence, capability registry, scope, and limits.
Deterministic: identical inputs produce identical plans.
No AI dependency. All decisions traceable to evidence.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
import hashlib
import json
from enum import Enum

# Import from other modules
from asta.capability import (
    CapabilityRegistry, ApplicabilityEvaluator, ApplicabilityResult,
    ApplicabilityState, Capability
)
from asta.taxonomy import (
    CanonicalCheckID, TestLevel, TAXONOMY_REGISTRY
)
from asta.models import Project, ProjectScope

# ==============================================================================
# Plan Data Structures
# ==============================================================================

class CheckState(str, Enum):
    """State of a check in the plan."""
    INCLUDED = "included"
    EXCLUDED = "excluded"
    BLOCKED = "blocked"
    UNSUPPORTED = "unsupported"
    NOT_APPLICABLE = "not_applicable"
    PENDING_RECOMMENDATION = "pending_recommendation"
    AWAITING_AUTHORIZATION = "awaiting_authorization"

@dataclass
class PlanCheck:
    """A check in the testing plan."""
    key: str                          # Canonical check ID string
    title: str                        # Human-readable title
    description: str                  # What this check does
    capability_id: str                # e.g., "pytest_unit"
    test_type: str                    # e.g., "unit", "api"
    domain: Optional[str] = None      # e.g., "backend"
    protocol: Optional[str] = None    # e.g., "https"
    technique: Optional[str] = None   # e.g., "api_test"
    validation_intent: Optional[str] = None  # e.g., "contract_compliance"
    state: str = "not_applicable"     # CheckState value as string
    reason: str = ""                  # Why this state
    prerequisites: List[str] = field(default_factory=list)
    risk_level: str = "low"           # low, medium, high, critical
    target: Optional[str] = None      # Target system/URL
    limits: Dict[str, Any] = field(default_factory=dict)
    evidence: List[str] = field(default_factory=list)
    adapter_id: str = ""              # e.g., "pytest_adapter"
    tool_versions: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "key": self.key,
            "title": self.title,
            "description": self.description,
            "capability_id": self.capability_id,
            "test_type": self.test_type,
            "domain": self.domain,
            "protocol": self.protocol,
            "technique": self.technique,
            "validation_intent": self.validation_intent,
            "state": self.state,
            "reason": self.reason,
            "prerequisites": self.prerequisites,
            "risk_level": self.risk_level,
            "target": self.target,
            "limits": self.limits,
            "evidence": self.evidence,
            "adapter_id": self.adapter_id,
            "tool_versions": self.tool_versions
        }

@dataclass
class PlanProvenance:
    """Provenance information for the plan."""
    generated_at: str
    generated_by: str = "asta-planner"
    scope_types: List[str] = field(default_factory=list)
    plan_revision: int = 1
    content_hash: str = ""
    ai_off: bool = True
    evidence_sources: List[str] = field(default_factory=list)  # e.g., ["inspection", "capability_registry"]
    policy_version: str = "1.0"

    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class Plan:
    """Versioned testing plan with provenance."""
    project_name: str
    plan_revision: int
    content_hash: str
    generated_at: str
    scope_types: List[str]
    risk_approval: str
    checks: List['PlanCheck']
    provenance: Dict
    ai_off: bool = True

    def to_dict(self) -> Dict:
        prov = self.provenance.to_dict() if hasattr(self.provenance, "to_dict") else self.provenance
        return {
            "project_name": self.project_name,
            "plan_revision": self.plan_revision,
            "content_hash": self.content_hash,
            "generated_at": self.generated_at,
            "scope_types": self.scope_types,
            "risk_approval": self.risk_approval,
            "checks": [c.to_dict() for c in self.checks],
            "provenance": prov,
            "ai_off": self.ai_off
        }

    def get_included_checks(self) -> List['PlanCheck']:
        return [c for c in self.checks if c.state == "included"]

    def get_excluded_checks(self) -> List['PlanCheck']:
        return [c for c in self.checks if c.state == "excluded"]

    def get_blocked_checks(self) -> List['PlanCheck']:
        return [c for c in self.checks if c.state == "blocked"]

    def get_unsupported_checks(self) -> List['PlanCheck']:
        return [c for c in self.checks if c.state == "unsupported"]

    def get_not_applicable_checks(self) -> List['PlanCheck']:
        return [c for c in self.checks if c.state == "not_applicable"]

    def get_pending_recommendation_checks(self) -> List['PlanCheck']:
        return [c for c in self.checks if c.state == "pending_recommendation"]

    def get_awaiting_authorization_checks(self) -> List['PlanCheck']:
        return [c for c in self.checks if c.state == "awaiting_authorization"]


# ==============================================================================
# Planner
# ==============================================================================

class DeterministicPlanner:
    """
    Deterministic planner that creates testing plans from evidence.
    Identical inputs always produce identical plans.
    """

    def __init__(self,
                 capability_registry: 'CapabilityRegistry',
                 taxonomy_registry: 'TaxonomyRegistry' = None):
        self.capability_registry = capability_registry
        self.taxonomy_registry = taxonomy_registry or TAXONOMY_REGISTRY
        self.evaluator = ApplicabilityEvaluator(capability_registry)

    def create_plan(self,
                    project: 'Project',
                    inspection_facts: List[Dict],
                    project_scope: ProjectScope,
                    authorization_manifest: Dict,
                    plan_revision: int = 1,
                    previous_plan_hash: str = None) -> 'Plan':
        """
        Create a deterministic testing plan.

        Args:
            project: Project object with profile, scope, config
            inspection_facts: List of inspection facts from static analysis
            project_scope: User-selected scope from ProjectScope
            authorization_manifest: Authorization manifest with allowed targets/risks
            plan_revision: Plan revision number
            previous_plan_hash: Hash of previous plan (for change detection)

        Returns:
            Plan object with all checks classified
        """
        # Evaluate all capabilities
        applicability_results = self.evaluator.evaluate_all_capabilities(
            inspection_facts=inspection_facts,
            project_scope=project_scope.to_dict(),
            authorization_manifest=authorization_manifest
        )

        # Create plan checks from applicability results
        checks = self._create_plan_checks(applicability_results, project_scope)

        # Apply user scope filtering
        checks = self._apply_scope_filter(checks, project_scope)

        # Generate provenance
        provenance = self._generate_provenance(
            project_name=project.name,
            plan_revision=plan_revision,
            scope_types=project_scope.types,
            risk_approval=project_scope.risk_approval,
            inspection_facts=inspection_facts,
            previous_plan_hash=previous_plan_hash
        )

        # Compute content hash
        content_hash = self._compute_content_hash(checks, provenance)

        # Create plan
        gen_at = provenance.generated_at if hasattr(provenance, "generated_at") else provenance["generated_at"]
        provenance.content_hash = content_hash
        plan = Plan(
            project_name=project.name,
            plan_revision=plan_revision,
            content_hash=content_hash,
            generated_at=gen_at,
            scope_types=project_scope.types,
            risk_approval=project_scope.risk_approval,
            checks=checks,
            provenance=provenance,
            ai_off=True
        )

        return plan

    def _create_plan_checks(self,
                            applicability_results: List['ApplicabilityResult'],
                            project_scope: ProjectScope) -> List['PlanCheck']:
        """Create PlanCheck objects from applicability results."""
        from asta.capability import ApplicabilityResult
        checks = []

        for result in applicability_results:
            capability = self.capability_registry.get(result.capability_id)
            if not capability:
                continue

            # Map applicability state to check state
            state = self._map_applicability_state(result.state)

            # Determine reason
            reason = result.reason
            if result.state == "Applicable":
                reason = "Applicable based on project evidence and scope"
            elif result.state == "Not applicable":
                reason = f"Not applicable: {result.reason}"
            elif result.state == "Unsupported":
                reason = f"Unsupported: {result.reason}"
            elif result.state == "Blocked":
                reason = f"Blocked: {result.reason}"
            elif result.state == "Awaiting authorization":
                reason = f"Awaiting authorization: {result.reason}"

            # Build canonical check ID
            canonical = self._build_canonical_check_id(capability)

            check = PlanCheck(
                key=str(canonical),
                title=capability.name,
                description=capability.description,
                capability_id=capability.capability_id,
                test_type=capability.test_types[0] if capability.test_types else "unknown",
                domain=canonical.domain.value if canonical.domain else None,
                protocol=canonical.protocol.value if canonical.protocol else None,
                technique=canonical.technique.value if canonical.technique else None,
                validation_intent=canonical.validation_intent.value if canonical.validation_intent else None,
                state=state,
                reason=reason,
                prerequisites=result.prerequisites,
                risk_level=capability.risk_level,
                target=self._get_target(capability),
                limits=capability.limits,
                evidence=result.evidence,
                adapter_id=capability.adapter_id,
                tool_versions=capability.tool_versions
            )

            checks.append(check)

        return checks

    def _map_applicability_state(self, state: str) -> str:
        """Map applicability state to check state."""
        mapping = {
            "Applicable": "included",
            "Not applicable": "not_applicable",
            "Unsupported": "unsupported",
            "Blocked": "blocked",
            "Awaiting authorization": "awaiting_authorization",
        }
        return mapping.get(state, "not_applicable")

    def _build_canonical_check_id(self, capability: 'Capability') -> 'CanonicalCheckID':
        """Build canonical check ID from capability."""
        # Use first test type as primary
        test_level = TestLevel(capability.test_types[0]) if capability.test_types else TestLevel.UNIT

        return CanonicalCheckID(
            test_level=test_level,
            taxonomy_version="1.0.0"
        )

    def _get_target(self, capability: 'Capability') -> Optional[str]:
        """Get target for capability."""
        if capability.capability_id in ["schemathesis_api", "httpx_api_assert"]:
            return "authorized_api_target"  # Will be resolved at execution
        return "local"

    def _apply_scope_filter(self, checks: List['PlanCheck'], project_scope: ProjectScope) -> List['PlanCheck']:
        """Filter checks to only those within user-approved scope."""
        filtered = []
        for check in checks:
            # Check if check's test_type is in user scope
            if check.test_type in project_scope.types:
                # Within scope - keep current state
                filtered.append(check)
            else:
                # Outside user scope - mark as excluded
                check.state = "excluded"
                check.reason = f"Outside user-approved scope (types: {', '.join(project_scope.types)})"
                filtered.append(check)
        return filtered

    def _generate_provenance(self,
                             project_name: str,
                             plan_revision: int,
                             scope_types: List[str],
                             risk_approval: str,
                             inspection_facts: List[Dict],
                             previous_plan_hash: str = None) -> PlanProvenance:
        """Generate provenance information."""
        return PlanProvenance(
            generated_at=datetime.utcnow().isoformat() + "Z",
            generated_by="asta-planner",
            scope_types=scope_types,
            plan_revision=plan_revision,
            evidence_sources=["inspection", "capability_registry"],
            policy_version="1.0",
            ai_off=True
        )

    def _compute_content_hash(self, checks: List['PlanCheck'], provenance: Any) -> str:
        """Compute deterministic content hash of plan."""
        content = ""
        # Sort checks by key for deterministic ordering
        for check in sorted(checks, key=lambda c: c.key):
            content += f"{check.key}{check.title}{check.state}{check.risk_level}"
        rev = provenance.plan_revision if hasattr(provenance, "plan_revision") else provenance.get('plan_revision', 1)
        scopes = provenance.scope_types if hasattr(provenance, "scope_types") else provenance.get('scope_types', [])
        content += f"{rev}{scopes}"
        return hashlib.sha256(content.encode()).hexdigest()


# ==============================================================================
# Plan Change Detection
# ==============================================================================

class PlanChangeDetector:
    """Detects changes between plan revisions."""

    @staticmethod
    def compare_plans(old_plan: Any, new_plan: Any) -> Dict[str, Any]:
        """Compare two plans and return change summary."""
        def _get_checks(p):
            checks = p.checks if hasattr(p, "checks") else p["checks"]
            res = {}
            for c in checks:
                k = c.key if hasattr(c, "key") else c["key"]
                res[k] = c
            return res

        def _get_val(obj, key, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        old_checks = _get_checks(old_plan)
        new_checks = _get_checks(new_plan)

        all_keys = set(old_checks.keys()) | set(new_checks.keys())

        added = []
        removed = []
        changed = []
        unchanged = []

        for key in all_keys:
            old = old_checks.get(key)
            new = new_checks.get(key)

            if old is None:
                added.append(key)
            elif new is None:
                removed.append(key)
            elif _get_val(old, "state") != _get_val(new, "state") or _get_val(old, "content_hash") != _get_val(new, "content_hash"):
                changed.append({
                    "key": key,
                    "old_state": _get_val(old, "state"),
                    "new_state": _get_val(new, "state")
                })
            else:
                unchanged.append(key)

        return {
            "added": added,
            "removed": removed,
            "changed": changed,
            "unchanged": unchanged,
            "total_old": len(old_checks),
            "total_new": len(new_checks)
        }

    @staticmethod
    def is_material_change(old_plan: Dict, new_plan: Dict) -> bool:
        """Check if plan change is material (requires re-approval)."""
        changes = PlanChangeDetector.compare_plans(old_plan, new_plan)
        # Material if any checks added, removed, or state changed
        return len(changes["added"]) > 0 or len(changes["removed"]) > 0 or len(changes["changed"]) > 0


# ==============================================================================
# Recommendation Engine
# ==============================================================================

class RecommendationEngine:
    """Generates evidence-backed recommendations for additional checks."""

    def __init__(self, capability_registry: 'CapabilityRegistry'):
        self.capability_registry = capability_registry

    def generate_recommendations(self,
                                 applicability_results: Any,
                                 project_scope: 'ProjectScope',
                                 project_profile: Dict) -> List[Dict]:
        """Generate recommendations for additional checks."""
        recommendations = []

        def _get(obj, key, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        for result in applicability_results:
            state = _get(result, "state")
            if state in ["Not applicable", "Unsupported"]:
                cap_id = _get(result, "capability_id")
                capability = self.capability_registry.get(cap_id)
                if not capability:
                    continue

                test_types = _get(capability, "test_types") or []
                scope_types = project_scope.types if hasattr(project_scope, "types") else project_scope.get("types", [])
                scope_overlap = set(test_types) & set(scope_types)
                if not scope_overlap:
                    continue

                name = _get(capability, "name")
                risk_level = _get(capability, "risk_level")
                desc = _get(capability, "description")
                reason = _get(result, "reason")
                evidence = _get(result, "evidence")
                prereqs = _get(result, "prerequisites")

                recommendation = {
                    "capability_id": cap_id,
                    "title": name,
                    "description": desc,
                    "rationale": f"Capability {name} could provide additional coverage for {', '.join(scope_overlap)} testing. Currently {state}: {reason}",
                    "evidence": evidence,
                    "risk_level": risk_level,
                    "prerequisites": prereqs,
                    "estimated_effort": self._estimate_effort(capability),
                    "test_types": list(scope_overlap),
                    "risk": risk_level
                }
                recommendations.append(recommendation)

        # Sort by risk level (low first) then by test type priority
        risk_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        recommendations.sort(key=lambda r: (risk_order.get(r["risk_level"], 99), r["title"]))

        return recommendations

    def _estimate_effort(self, capability: Any) -> str:
        """Estimate effort to enable capability."""
        if isinstance(capability, dict):
            prereqs = capability.get("prerequisites", [])
        else:
            prereqs = getattr(capability, "prerequisites", [])
        missing_prereqs = len(prereqs)
        if missing_prereqs == 0:
            return "low"
        elif missing_prereqs <= 2:
            return "medium"
        else:
            return "high"


# ==============================================================================
# Public API
# ==============================================================================

def create_plan(project: 'Project',
                inspection_facts: List[Dict],
                project_scope: 'ProjectScope',
                authorization_manifest: Dict,
                plan_revision: int = 1,
                previous_plan_hash: str = None) -> Dict:
    """Main entry point for plan creation."""
    from asta.capability import CapabilityRegistry

    registry = CapabilityRegistry()
    planner = DeterministicPlanner(registry)
    return planner.create_plan(
        project=project,
        inspection_facts=inspection_facts,
        project_scope=project_scope,
        authorization_manifest=authorization_manifest,
        plan_revision=plan_revision,
        previous_plan_hash=previous_plan_hash
    )

def generate_recommendations(plan: Dict,
                             project_scope: 'ProjectScope',
                             project_profile: Dict) -> List[Dict]:
    """Generate recommendations for a plan."""
    from asta.capability import CapabilityRegistry, ApplicabilityEvaluator

    registry = CapabilityRegistry()
    evaluator = ApplicabilityEvaluator(registry)

    # Re-evaluate to get full applicability results
    # (In production, these would be cached from plan creation)
    applicability_results = evaluator.evaluate_all_capabilities(
        inspection_facts=[],  # Would be passed in real usage
        project_scope=project_scope.to_dict(),
        authorization_manifest={}
    )

    engine = RecommendationEngine(registry)
    return engine.generate_recommendations(applicability_results, project_scope, project_profile)


# ==============================================================================
# CLI Integration
# ==============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Simple test
        from asta.capability import CapabilityRegistry
        registry = CapabilityRegistry()
        print(f"Registry has {len(registry.capabilities)} capabilities")
        for cap in registry.list_all():
            print(f"  {cap.capability_id}: {cap.name} ({cap.test_types})")