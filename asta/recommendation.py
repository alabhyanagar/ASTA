#!/usr/bin/env python3
"""
ASTA M1 Recommendation Review and Exact Approval Binding

Each recommendation includes rationale/evidence/risk/prerequisites.
Approved additions bind to run, exact scope, plan revision/content hash and policy version.
Declined/pending additions never execute.
Material change invalidates approval and is audited.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
import hashlib
import json
import secrets

# Import from other modules
from asta.planner import Plan, PlanCheck
from asta.capability import CapabilityRegistry, Capability

# ==============================================================================
# Recommendation Data Structures
# ==============================================================================

class RecommendationStatus(str, Enum):
    """Status of a recommendation."""
    PENDING = "pending"           # Awaiting user review
    APPROVED = "approved"         # User approved for inclusion
    DECLINED = "declined"         # User explicitly declined
    DEFERRED = "deferred"         # Deferred to future run

class RecommendationType(str, Enum):
    """Type of recommendation."""
    ADDITIONAL_CHECK = "additional_check"        # Add a new capability/check
    SCOPE_EXPANSION = "scope_expansion"          # Expand scope to include new types
    CONFIGURATION_CHANGE = "configuration_change" # Change configuration
    PREREQUISITE_INSTALL = "prerequisite_install" # Install prerequisite

@dataclass
class Recommendation:
    """A recommendation for additional checks or scope changes."""
    recommendation_id: str
    type: str
    capability_id: str
    title: str
    description: str
    rationale: str                           # Why this is recommended
    evidence: List[str] = field(default_factory=list)  # Evidence supporting recommendation
    risk_level: str = "low"                  # low, medium, high, critical
    prerequisites: List[str] = field(default_factory=list)
    estimated_effort: str = "medium"         # low, medium, high
    test_types: List[str] = field(default_factory=list)
    status: str = "pending"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    reviewed_at: Optional[str] = None
    reviewed_by: Optional[str] = None
    review_decision: Optional[str] = None    # approved/declined/deferred

    def to_dict(self) -> Dict:
        return {
            "recommendation_id": self.recommendation_id,
            "type": self.type,
            "capability_id": self.capability_id,
            "title": self.title,
            "description": self.description,
            "rationale": self.rationale,
            "evidence": self.evidence,
            "risk_level": self.risk_level,
            "prerequisites": self.prerequisites,
            "estimated_effort": self.estimated_effort,
            "test_types": self.test_types,
            "status": self.status,
            "created_at": self.created_at,
            "reviewed_at": self.reviewed_at,
            "reviewed_by": self.reviewed_by,
            "review_decision": self.review_decision
        }

@dataclass
class ApprovalBinding:
    """
    Exact approval binding to run, scope, plan revision, content hash, and policy version.
    Material changes invalidate this binding.
    """
    binding_id: str
    plan_content_hash: str
    plan_revision: int
    project_name: str
    scope_types: List[str]
    risk_approval: str
    policy_version: str
    approved_checks: List[str] = field(default_factory=list)  # Check keys
    excluded_checks: List[str] = field(default_factory=list)
    approved_recommendations: List[str] = field(default_factory=list)  # recommendation_ids
    declined_recommendations: List[str] = field(default_factory=list)
    deferred_recommendations: List[str] = field(default_factory=list)
    approved_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    approved_by: str = ""
    valid: bool = True
    invalidation_reason: Optional[str] = None
    invalidated_at: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "binding_id": self.binding_id,
            "plan_content_hash": self.plan_content_hash,
            "plan_revision": self.plan_revision,
            "project_name": self.project_name,
            "scope_types": self.scope_types,
            "risk_approval": self.risk_approval,
            "policy_version": self.policy_version,
            "approved_checks": self.approved_checks,
            "excluded_checks": self.excluded_checks,
            "approved_recommendations": self.approved_recommendations,
            "declined_recommendations": self.declined_recommendations,
            "deferred_recommendations": self.deferred_recommendations,
            "approved_at": self.approved_at,
            "approved_by": self.approved_by,
            "valid": self.valid,
            "invalidation_reason": self.invalidation_reason,
            "invalidated_at": self.invalidated_at
        }


# ==============================================================================
# Recommendation Manager
# ==============================================================================

class RecommendationManager:
    """Manages recommendations and their review/approval lifecycle."""

    def __init__(self, capability_registry: 'CapabilityRegistry'):
        self.capability_registry = capability_registry
        self.recommendations: Dict[str, 'Recommendation'] = {}

    def create_recommendations(self,
                               plan_checks: List[Dict],
                               capability_registry: 'CapabilityRegistry',
                               project_scope: 'ProjectScope',
                               project_profile: Dict) -> List[Dict]:
        """Create recommendations from plan checks with NOT_APPLICABLE/UNSUPPORTED states."""
        from asta.planner import PlanCheck, CheckState

        def _get(obj, key, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        recommendations = []

        for check in plan_checks:
            state = _get(check, "state")
            if state not in ["not_applicable", "unsupported"]:
                continue

            cap_id = _get(check, "capability_id")
            capability = capability_registry.get(cap_id)
            if not capability:
                continue

            test_types = _get(capability, "test_types", [])
            scope_types = project_scope.types if hasattr(project_scope, "types") else project_scope.get("types", [])
            scope_overlap = set(test_types) & set(scope_types)
            if not scope_overlap:
                continue

            rec_id = self._generate_recommendation_id(capability.capability_id)
            reason = _get(check, "reason", "")
            evidence = _get(check, "evidence", [])

            recommendation = Recommendation(
                recommendation_id=rec_id,
                type="additional_check",
                capability_id=capability.capability_id,
                title=capability.name,
                description=capability.description,
                rationale=f"Capability {capability.name} could provide additional coverage for {', '.join(scope_overlap)} testing. Currently {state}: {reason}",
                evidence=evidence,
                risk_level=capability.risk_level,
                prerequisites=capability.prerequisites,
                estimated_effort=self._estimate_effort(capability),
                test_types=list(scope_overlap)
            )

            self.recommendations[rec_id] = recommendation
            recommendations.append(recommendation)

        return recommendations

    def _generate_recommendation_id(self, capability_id: str) -> str:
        """Generate unique recommendation ID."""
        content = f"{capability_id}{datetime.utcnow().isoformat()}"
        return f"rec_{hashlib.sha256(content.encode()).hexdigest()[:12]}"

    def _estimate_effort(self, capability: 'Capability') -> str:
        """Estimate effort to enable capability."""
        missing_prereqs = len(capability.prerequisites)
        if missing_prereqs == 0:
            return "low"
        elif missing_prereqs <= 2:
            return "medium"
        else:
            return "high"

    def get_recommendation(self, recommendation_id: str) -> Optional['Recommendation']:
        return self.recommendations.get(recommendation_id)

    def list_pending_recommendations(self) -> List['Recommendation']:
        return [r for r in self.recommendations.values() if r.status == "pending"]

    def review_recommendation(self,
                              recommendation_id: str,
                              decision: str,  # approved/declined/deferred
                              reviewer: str,
                              reason: str = "") -> bool:
        """Record user's review decision for a recommendation."""
        rec = self.recommendations.get(recommendation_id)
        if not rec:
            return False

        if decision not in ["approved", "declined", "deferred"]:
            return False

        rec.status = decision
        rec.reviewed_at = datetime.utcnow().isoformat() + "Z"
        rec.reviewed_by = reviewer
        rec.review_decision = decision

        return True

    def get_approved_recommendations(self) -> List['Recommendation']:
        return [r for r in self.recommendations.values() if r.status == "approved"]

    def get_declined_recommendations(self) -> List['Recommendation']:
        return [r for r in self.recommendations.values() if r.status == "declined"]


# ==============================================================================
# Approval Binding Manager
# ==============================================================================

class ApprovalBindingManager:
    """Manages exact approval bindings with invalidation on material changes."""

    def __init__(self):
        self.bindings: Dict[str, 'ApprovalBinding'] = {}

    def create_binding(self,
                       plan: Dict,
                       project_name: str,
                       scope_types: List[str],
                       risk_approval: str,
                       approved_checks: List[str],
                       excluded_checks: List[str],
                       approved_recommendations: List[str],
                       declined_recommendations: List[str],
                       deferred_recommendations: List[str],
                       approved_by: str) -> 'ApprovalBinding':
        """Create an approval binding for a plan."""

        content_hash = plan.content_hash if hasattr(plan, "content_hash") else plan["content_hash"]
        plan_rev = plan.plan_revision if hasattr(plan, "plan_revision") else plan["plan_revision"]
        scope_types = plan.scope_types if hasattr(plan, "scope_types") else plan["scope_types"]
        prov = plan.provenance if hasattr(plan, "provenance") else plan["provenance"]
        policy_ver = prov.policy_version if hasattr(prov, "policy_version") else prov["policy_version"]

        timestamp = datetime.utcnow().isoformat()
        binding_id = f"bind_{hashlib.sha256(f'{content_hash}{timestamp}'.encode()).hexdigest()[:12]}"

        binding = ApprovalBinding(
            binding_id=binding_id,
            plan_content_hash=content_hash,
            plan_revision=plan_rev,
            project_name=project_name,
            scope_types=scope_types,
            risk_approval=risk_approval,
            policy_version=policy_ver,
            approved_checks=approved_checks,
            excluded_checks=excluded_checks,
            approved_recommendations=approved_recommendations,
            declined_recommendations=declined_recommendations,
            deferred_recommendations=deferred_recommendations,
            approved_by=approved_by
        )

        self.bindings[binding_id] = binding
        return binding

    def get_binding(self, binding_id: str) -> Optional['ApprovalBinding']:
        return self.bindings.get(binding_id)

    def get_latest_binding(self, project_name: str) -> Optional['ApprovalBinding']:
        """Get the latest binding for a project."""
        def _get_name(b):
            return b.project_name if hasattr(b, "project_name") else b["project_name"]
        def _get_approved_at(b):
            return b.approved_at if hasattr(b, "approved_at") else b["approved_at"]

        project_bindings = [b for b in self.bindings.values() if _get_name(b) == project_name]
        if not project_bindings:
            return None
        return max(project_bindings, key=_get_approved_at)

    def validate_binding(self, binding: 'ApprovalBinding', plan: Any) -> Tuple[bool, str]:
        """
        Validate if an approval binding is still valid for a plan.
        Returns (is_valid, reason_if_invalid).
        """
        content_hash = plan.content_hash if hasattr(plan, "content_hash") else plan["content_hash"]
        plan_rev = plan.plan_revision if hasattr(plan, "plan_revision") else plan["plan_revision"]
        scope_types = plan.scope_types if hasattr(plan, "scope_types") else plan["scope_types"]
        prov = plan.provenance if hasattr(plan, "provenance") else plan["provenance"]
        policy_ver = prov.policy_version if hasattr(prov, "policy_version") else prov["policy_version"]

        # Check plan content hash matches
        if binding.plan_content_hash != content_hash:
            return False, f"Plan content hash changed: {binding.plan_content_hash[:8]}... -> {content_hash[:8]}..."

        # Check plan revision matches
        if binding.plan_revision != plan_rev:
            return False, f"Plan revision changed: {binding.plan_revision} -> {plan_rev}"

        # Check scope types match
        if set(binding.scope_types) != set(scope_types):
            return False, f"Scope types changed: {binding.scope_types} -> {scope_types}"

        # Check policy version
        if binding.policy_version != policy_ver:
            return False, f"Policy version changed: {binding.policy_version} -> {policy_ver}"

        # Check if binding was invalidated
        if not binding.valid:
            return False, f"Binding invalidated: {binding.invalidation_reason}"

        return True, "Valid"

    def invalidate_binding(self, binding_id: str, reason: str) -> bool:
        """Invalidate a binding due to material change."""
        binding = self.bindings.get(binding_id)
        if not binding:
            return False

        binding.valid = False
        binding.invalidation_reason = reason
        binding.invalidated_at = datetime.utcnow().isoformat() + "Z"
        return True

    def check_and_invalidate_on_change(self,
                                        binding_id: str,
                                        old_plan: Dict,
                                        new_plan: Dict) -> Tuple[bool, str]:
        """
        Check if plan change invalidates the binding.
        Returns (was_invalidated, reason).
        """
        from asta.planner import PlanChangeDetector

        binding = self.bindings.get(binding_id)
        if not binding:
            return False, "Binding not found"

        # Check for material changes
        changes = PlanChangeDetector.compare_plans(old_plan, new_plan)

        if PlanChangeDetector.is_material_change(old_plan, new_plan):
            reason = f"Material change detected: {len(changes['added'])} added, {len(changes['removed'])} removed, {len(changes['changed'])} changed"
            self.invalidate_binding(binding_id, reason)
            return True, reason

        return False, "No material change"


# ==============================================================================
# Recommendation Review Workflow
# ==============================================================================

class RecommendationReviewWorkflow:
    """Orchestrates the recommendation review and approval binding process."""

    def __init__(self,
                 capability_registry: 'CapabilityRegistry',
                 project_path: Path):
        self.capability_registry = capability_registry
        self.project_path = project_path
        self.rec_manager = RecommendationManager(capability_registry)
        self.binding_manager = ApprovalBindingManager()

        # Load existing data from project workspace
        self._load_from_workspace()

    def _load_from_workspace(self):
        """Load recommendations and bindings from project workspace."""
        workspace = self.project_path / ".asta" / "recommendations"
        if not workspace.exists():
            return

        # Load recommendations
        recs_file = workspace / "recommendations.json"
        if recs_file.exists():
            data = json.loads(recs_file.read_text())
            for rec_data in data:
                rec = Recommendation(**rec_data)
                self.rec_manager.recommendations[rec.recommendation_id] = rec

        # Load bindings
        bindings_file = workspace / "approval_bindings.json"
        if bindings_file.exists():
            data = json.loads(bindings_file.read_text())
            for bind_data in data:
                binding = ApprovalBinding(**bind_data)
                self.binding_manager.bindings[binding.binding_id] = binding

    def _save_to_workspace(self):
        """Save recommendations and bindings to project workspace."""
        workspace = self.project_path / ".asta" / "recommendations"
        workspace.mkdir(parents=True, exist_ok=True)

        # Save recommendations
        recs_file = workspace / "recommendations.json"
        recs_file.write_text(json.dumps([r.to_dict() for r in self.rec_manager.recommendations.values()], indent=2))

        # Save bindings
        bindings_file = workspace / "approval_bindings.json"
        bindings_file.write_text(json.dumps([b.to_dict() for b in self.binding_manager.bindings.values()], indent=2))

    def generate_recommendations_for_plan(self,
                                          plan: Any,
                                          project_scope: 'ProjectScope',
                                          project_profile: Dict) -> List[Dict]:
        """Generate recommendations for a plan."""
        checks = plan.checks if hasattr(plan, "checks") else plan["checks"]
        recommendations = self.rec_manager.create_recommendations(
            plan_checks=checks,
            capability_registry=self.capability_registry,
            project_scope=project_scope,
            project_profile=project_profile
        )
        self._save_to_workspace()
        return recommendations

    def present_recommendations_for_review(self, plan: Dict) -> List[Dict]:
        """Get pending recommendations for user review."""
        pending = self.rec_manager.list_pending_recommendations()

        if not pending:
            print("No pending recommendations.")
            return []

        print(f"=== Pending Recommendations ({len(pending)}) ===")
        for i, rec in enumerate(pending, 1):
            print(f"\n{i}. {rec.title} ({rec.capability_id})")
            print(f"   Type: {rec.type}")
            print(f"   Risk: {rec.risk_level}")
            print(f"   Effort: {rec.estimated_effort}")
            print(f"   Test Types: {', '.join(rec.test_types)}")
            print(f"   Rationale: {rec.rationale}")
            if rec.prerequisites:
                print(f"   Prerequisites: {', '.join(rec.prerequisites)}")
            if rec.evidence:
                print(f"   Evidence: {', '.join(rec.evidence[:3])}{'...' if len(rec.evidence) > 3 else ''}")

        return pending

    def review_recommendations_interactive(self, plan: Dict, reviewer: str) -> Dict[str, str]:
        """Interactive recommendation review (CLI integration)."""
        pending = self.rec_manager.list_pending_recommendations()

        if not pending:
            return {}

        decisions = {}

        for rec in pending:
            print(f"\n--- Recommendation: {rec.title} ---")
            print(f"Risk: {rec.risk_level} | Effort: {rec.estimated_effort}")
            print(f"Rationale: {rec.rationale}")
            print(f"Prerequisites: {', '.join(rec.prerequisites) if rec.prerequisites else 'none'}")

            decision = input("Decision (approve/decline/defer): ").strip().lower()
            while decision not in ["approve", "decline", "defer"]:
                decision = input("Please enter 'approve', 'decline', or 'defer': ").strip().lower()

            reason = ""
            if decision == "decline":
                reason = input("Reason for declining (optional): ").strip()

            self.rec_manager.review_recommendation(
                recommendation_id=rec.recommendation_id,
                decision=decision,
                reviewer=reviewer,
                reason=reason
            )

            decisions[rec.recommendation_id] = decision

        self._save_to_workspace()
        return decisions

    def create_approval_binding(self,
                                plan: Dict,
                                project_name: str,
                                scope_types: List[str],
                                risk_approval: str,
                                approved_checks: List[str],
                                excluded_checks: List[str],
                                reviewer: str) -> Dict:
        """Create approval binding after recommendation review."""

        # Get recommendation decisions
        approved_recs = self.rec_manager.get_approved_recommendations()
        declined_recs = self.rec_manager.get_declined_recommendations()
        deferred_recs = [r for r in self.rec_manager.recommendations.values()
                        if r.status == "deferred"]

        # Determine approved checks (included + approved recommendations)
        all_approved_checks = list(approved_checks)
        for rec in approved_recs:
            cap = self.capability_registry.get(rec.capability_id)
            if cap:
                all_approved_checks.append(f"{cap.capability_id}_recommended")

        binding = self.binding_manager.create_binding(
            plan=plan,
            project_name=project_name,
            scope_types=scope_types,
            risk_approval=risk_approval,
            approved_checks=all_approved_checks,
            excluded_checks=excluded_checks,
            approved_recommendations=[r.recommendation_id for r in approved_recs],
            declined_recommendations=[r.recommendation_id for r in declined_recs],
            deferred_recommendations=[r.recommendation_id for r in deferred_recs],
            approved_by=reviewer
        )

        self._save_to_workspace()
        return binding

    def validate_existing_binding(self, plan: Dict, project_name: str) -> Tuple[bool, str]:
        """Validate if existing binding is still valid for current plan."""
        binding = self.binding_manager.get_latest_binding(project_name)
        if not binding:
            return False, "No existing approval binding found"

        return self.binding_manager.validate_binding(binding, plan)

    def get_audit_trail(self) -> List[Dict]:
        """Get complete audit trail of recommendations and bindings."""
        trail = []

        for rec in self.rec_manager.recommendations.values():
            trail.append({
                "type": "recommendation",
                "recommendation_id": rec.recommendation_id,
                "title": rec.title,
                "status": rec.status,
                "created_at": rec.created_at,
                "reviewed_at": rec.reviewed_at,
                "reviewed_by": rec.reviewed_by,
                "decision": rec.review_decision
            })

        for binding in self.binding_manager.bindings.values():
            trail.append({
                "type": "approval_binding",
                "binding_id": binding.binding_id,
                "plan_content_hash": binding.plan_content_hash[:12] + "...",
                "plan_revision": binding.plan_revision,
                "approved_at": binding.approved_at,
                "approved_by": binding.approved_by,
                "valid": binding.valid,
                "invalidation_reason": binding.invalidation_reason
            })

        return sorted(trail, key=lambda x: x.get("created_at", x.get("approved_at", "")))


# ==============================================================================
# Public API
# ==============================================================================

def create_recommendation_manager(capability_registry: 'CapabilityRegistry') -> RecommendationManager:
    return RecommendationManager(capability_registry)

def create_approval_binding_manager() -> ApprovalBindingManager:
    return ApprovalBindingManager()

def create_recommendation_workflow(capability_registry: 'CapabilityRegistry',
                                   project_path: Path) -> RecommendationReviewWorkflow:
    return RecommendationReviewWorkflow(capability_registry, project_path)


# ==============================================================================
# CLI Integration
# ==============================================================================

def approve_command(path: str, confirm_all: bool = False, show_plan: bool = False):
    """CLI command for reviewing and approving checks."""
    from asta.models import Project, ProjectScope
    from asta.capability import CapabilityRegistry
    from asta.inspection import inspect_project

    if path is None:
        path = click.prompt('Project path', type=click.Path(exists=True))

    approve_command_impl(path=path, confirm_all=confirm_all, show_plan=show_plan)

def approve_command_impl(path: str, confirm_all: bool = False, show_plan: bool = False):
    """Review and approve checks; high-risk checks await separate authorization."""
    from asta.approval import approve_command as _approve_command

    _approve_command(path=path, confirm_all=confirm_all, show_plan=show_plan)

# ==============================================================================
# CLI Integration
# ==============================================================================

if __name__ == "__main__":
    import sys
    from pathlib import Path

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        from asta.capability import CapabilityRegistry
        registry = CapabilityRegistry()
        manager = RecommendationManager(registry)
        print(f"RecommendationManager created with {len(registry.capabilities)} capabilities")