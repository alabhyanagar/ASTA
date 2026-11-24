#!/usr/bin/env python3
"""
ASTA M1 Deterministic Planner Tests
"""

import pytest
import json
import tempfile
from pathlib import Path
import sys
from typing import List, Dict, Optional, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from asta.planner import (
    DeterministicPlanner, Plan, PlanCheck, PlanProvenance,
    CheckState, PlanChangeDetector, RecommendationEngine,
    create_plan
)
from asta.capability import CapabilityRegistry, ApplicabilityState
from asta.taxonomy import TestLevel, TAXONOMY_REGISTRY
from asta.models import Project, ProjectScope, ProjectProfile, ProjectConfig, ProjectCredentials, ProjectDependencies


class TestDeterministicPlanner:
    """Test the deterministic planner."""

    def create_sample_project(self) -> Project:
        """Create a sample project for testing."""
        profile = ProjectProfile(
            detected_type="python",
            language="python",
            frameworks=["FastAPI", "pytest"],
            manifests=["pyproject.toml"],
            test_commands=["pytest"],
            confidence=0.9
        )

        scope = ProjectScope(types=["unit", "integration", "api"], risk_approval="high")
        config = ProjectConfig(timeout_seconds=300, max_workers=1)

        project = Project(
            id="proj_test123",
            name="test-project",
            source_path="/tmp/test-project",
            created_at="2026-11-23T00:00:00Z",
            updated_at="2026-11-23T00:00:00Z",
            profile=profile,
            scope=scope,
            config=config,
            credentials=ProjectCredentials(),
            dependencies=ProjectDependencies()
        )
        return project

    def create_inspection_facts(self) -> List[Dict]:
        """Create sample inspection facts."""
        return [
            {"category": "language", "name": "python", "confidence": "high", "evidence": ["pyproject.toml"]},
            {"category": "language", "name": "primary", "value": "python", "confidence": "high", "evidence": []},
            {"category": "manifest", "name": "pyproject.toml", "confidence": "high", "evidence": ["Found pyproject.toml"]},
            {"category": "framework", "name": "pytest", "confidence": "high", "evidence": ["Found in pyproject.toml"]},
            {"category": "tool", "name": "pytest", "confidence": "high", "evidence": ["Found in pyproject.toml [tool.pytest]"]},
            {"category": "test_file", "name": "python test files", "value": "5", "confidence": "high", "evidence": ["Found 5 files matching test_*.py"]},
            {"category": "test_file", "name": "python integration test files", "value": "2", "confidence": "high", "evidence": ["Found 2 files matching *integration*.py"]},
            {"category": "test_command", "name": "pytest", "confidence": "medium", "evidence": ["Inferred from pyproject.toml"]},
        ]

    def create_authorization_manifest(self) -> Dict:
        return {
            "allowed_targets": ["https://api.example.com"],
            "authorized_risks": ["low", "medium", "high"]
        }

    def test_planner_creates_plan(self):
        """Planner creates a plan with all capabilities evaluated."""
        project = self.create_sample_project()
        facts = self.create_inspection_facts()
        scope = project.scope
        auth = self.create_authorization_manifest()

        registry = CapabilityRegistry()
        planner = DeterministicPlanner(registry)

        plan = planner.create_plan(
            project=project,
            inspection_facts=facts,
            project_scope=scope,
            authorization_manifest=auth,
            plan_revision=1
        )

        assert isinstance(plan, Plan)
        assert plan.project_name == "test-project"
        assert plan.plan_revision == 1
        assert len(plan.content_hash) == 64  # SHA256 hex
        assert plan.ai_off == True
        assert len(plan.checks) > 0
        assert plan.provenance.ai_off == True

    def test_plan_has_all_capabilities_evaluated(self):
        """Plan includes all registered capabilities."""
        project = self.create_sample_project()
        facts = self.create_inspection_facts()
        scope = project.scope
        auth = self.create_authorization_manifest()

        registry = CapabilityRegistry()
        planner = DeterministicPlanner(registry)

        plan = planner.create_plan(project, facts, scope, auth)

        # Should have 4 checks (one per capability)
        assert len(plan.checks) == 4

        capability_ids = {c.capability_id for c in plan.checks}
        assert "pytest_unit" in capability_ids
        assert "pytest_integration" in capability_ids
        assert "schemathesis_api" in capability_ids
        assert "httpx_api_assert" in capability_ids

    def test_plan_states_classified(self):
        """Checks are properly classified by state."""
        project = self.create_sample_project()
        facts = self.create_inspection_facts()
        scope = project.scope
        auth = self.create_authorization_manifest()

        registry = CapabilityRegistry()
        planner = DeterministicPlanner(registry)

        plan = planner.create_plan(project, facts, scope, auth)

        # pytest_unit should be INCLUDED (all signals present)
        pytest_unit = next(c for c in plan.checks if c.capability_id == "pytest_unit")
        assert pytest_unit.state == "included"

        # pytest_integration should be INCLUDED (integration tests present)
        pytest_int = next(c for c in plan.checks if c.capability_id == "pytest_integration")
        assert pytest_int.state == "included"

        # schemathesis_api should be NOT_APPLICABLE (no OpenAPI spec)
        schemathesis = next(c for c in plan.checks if c.capability_id == "schemathesis_api")
        assert schemathesis.state == "not_applicable"

        # httpx_api_assert: if api is in scope and target authorized, it's included; if api not in scope, excluded
        httpx = next(c for c in plan.checks if c.capability_id == "httpx_api_assert")
        assert httpx.state in ["included", "not_applicable"]

    def test_plan_deterministic(self):
        """Identical inputs produce identical plans."""
        project = self.create_sample_project()
        facts = self.create_inspection_facts()
        scope = project.scope
        auth = self.create_authorization_manifest()

        registry = CapabilityRegistry()
        planner = DeterministicPlanner(registry)

        plan1 = planner.create_plan(project, facts, scope, auth, plan_revision=1)
        plan2 = planner.create_plan(project, facts, scope, auth, plan_revision=1)

        # Content hashes should be identical
        assert plan1.content_hash == plan2.content_hash

        # All check states identical
        for c1, c2 in zip(sorted(plan1.checks, key=lambda c: c.key),
                          sorted(plan2.checks, key=lambda c: c.key)):
            assert c1.state == c2.state
            assert c1.reason == c2.reason

    def test_plan_provenance(self):
        """Plan has complete provenance."""
        project = self.create_sample_project()
        facts = self.create_inspection_facts()
        scope = project.scope
        auth = self.create_authorization_manifest()

        registry = CapabilityRegistry()
        planner = DeterministicPlanner(registry)

        plan = planner.create_plan(project, facts, scope, auth, plan_revision=3)

        assert plan.provenance.generated_by == "asta-planner"
        assert plan.provenance.plan_revision == 3
        assert plan.provenance.ai_off == True
        assert plan.provenance.policy_version == "1.0"
        assert "inspection" in plan.provenance.evidence_sources
        assert "capability_registry" in plan.provenance.evidence_sources


class TestPlanCheck:
    """Test PlanCheck data structure."""

    def test_plan_check_creation(self):
        """PlanCheck can be created with all fields."""
        check = PlanCheck(
            key="Check(test_level=unit)",
            title="Python Unit Testing (pytest)",
            description="Execute existing pytest unit tests",
            capability_id="pytest_unit",
            test_type="unit",
            state="included",
            reason="All required signals satisfied",
            prerequisites=["pytest>=8.2.0"],
            risk_level="low",
            target="local",
            limits={"timeout_seconds": 300},
            evidence=["pyproject.toml", "pytest.ini"],
            adapter_id="pytest_adapter",
            tool_versions={"pytest": "8.2.0"}
        )

        assert check.key == "Check(test_level=unit)"
        assert check.capability_id == "pytest_unit"
        assert check.state == "included"
        assert check.risk_level == "low"

    def test_plan_check_to_dict(self):
        """PlanCheck serializes to dict."""
        check = PlanCheck(
            key="test",
            title="Test",
            description="Desc",
            capability_id="cap1",
            test_type="unit",
            state="included",
            reason="Reason",
            risk_level="low"
        )

        data = check.to_dict()

        assert data["key"] == "test"
        assert data["state"] == "included"
        assert data["capability_id"] == "cap1"


class TestPlanChangeDetector:
    """Test plan change detection."""

    def create_plan_with_checks(self, checks: List[Dict], revision: int = 1) -> Dict:
        """Helper to create a plan with given checks."""
        provenance = PlanProvenance(
            generated_at="2026-11-23T00:00:00Z",
            plan_revision=revision,
            scope_types=["unit"],
            content_hash="hash"
        )
        return {
            "project_name": "test",
            "plan_revision": revision,
            "content_hash": "hash",
            "generated_at": "2026-11-23T00:00:00Z",
            "scope_types": ["unit"],
            "risk_approval": "high",
            "checks": checks,
            "provenance": provenance
        }

    def test_detect_added_checks(self):
        """Detect added checks between revisions."""
        old_checks = [
            {"key": "check1", "title": "Check 1", "description": "", "capability_id": "c1", "test_type": "unit", "state": "included", "reason": "", "risk_level": "low"}
        ]
        new_checks = [
            {"key": "check1", "title": "Check 1", "description": "", "capability_id": "c1", "test_type": "unit", "state": "included", "reason": "", "risk_level": "low"},
            {"key": "check2", "title": "Check 2", "description": "", "capability_id": "c2", "test_type": "integration", "state": "included", "reason": "", "risk_level": "medium"}
        ]

        old_plan = self.create_plan_with_checks(old_checks, 1)
        new_plan = self.create_plan_with_checks(new_checks, 2)

        changes = PlanChangeDetector.compare_plans(old_plan, new_plan)

        assert "check2" in changes["added"]
        assert len(changes["removed"]) == 0
        assert len(changes["changed"]) == 0
        assert "check1" in changes["unchanged"]

    def test_detect_removed_checks(self):
        """Detect removed checks."""
        old_checks = [
            {"key": "check1", "title": "Check 1", "description": "", "capability_id": "c1", "test_type": "unit", "state": "included", "reason": "", "risk_level": "low"},
            {"key": "check2", "title": "Check 2", "description": "", "capability_id": "c2", "test_type": "integration", "state": "included", "reason": "", "risk_level": "medium"}
        ]
        new_checks = [
            {"key": "check1", "title": "Check 1", "description": "", "capability_id": "c1", "test_type": "unit", "state": "included", "reason": "", "risk_level": "low"}
        ]

        old_plan = self.create_plan_with_checks(old_checks, 1)
        new_plan = self.create_plan_with_checks(new_checks, 2)

        changes = PlanChangeDetector.compare_plans(old_plan, new_plan)

        assert "check2" in changes["removed"]
        assert len(changes["added"]) == 0

    def test_detect_state_changes(self):
        """Detect state changes."""
        old_checks = [
            {"key": "check1", "title": "Check 1", "description": "", "capability_id": "c1", "test_type": "unit", "state": "included", "reason": "", "risk_level": "low"}
        ]
        new_checks = [
            {"key": "check1", "title": "Check 1", "description": "", "capability_id": "c1", "test_type": "unit", "state": "blocked", "reason": "Missing prerequisite", "risk_level": "low"}
        ]

        old_plan = self.create_plan_with_checks(old_checks, 1)
        new_plan = self.create_plan_with_checks(new_checks, 2)

        changes = PlanChangeDetector.compare_plans(old_plan, new_plan)

        assert len(changes["changed"]) == 1
        assert changes["changed"][0]["key"] == "check1"
        assert changes["changed"][0]["old_state"] == "included"
        assert changes["changed"][0]["new_state"] == "blocked"

    def test_material_change_detection(self):
        """Material change requires re-approval."""
        old_checks = [
            {"key": "check1", "title": "Check 1", "description": "", "capability_id": "c1", "test_type": "unit", "state": "included", "reason": "", "risk_level": "low"}
        ]
        new_checks = [
            {"key": "check1", "title": "Check 1", "description": "", "capability_id": "c1", "test_type": "unit", "state": "included", "reason": "", "risk_level": "low"},
            {"key": "check2", "title": "Check 2", "description": "", "capability_id": "c2", "test_type": "integration", "state": "included", "reason": "", "risk_level": "medium"}
        ]

        old_plan = self.create_plan_with_checks(old_checks, 1)
        new_plan = self.create_plan_with_checks(new_checks, 2)

        assert PlanChangeDetector.is_material_change(old_plan, new_plan) == True

        # No change should not be material
        assert PlanChangeDetector.is_material_change(old_plan, old_plan) == False


class TestRecommendationEngine:
    """Test recommendation engine."""

    def test_generate_recommendations(self):
        """Generate recommendations for not applicable capabilities."""
        from asta.capability import CapabilityRegistry, ApplicabilityResult, ApplicabilityState

        registry = CapabilityRegistry()
        engine = RecommendationEngine(registry)

        # Create applicability results with one not applicable
        results = [
            ApplicabilityResult(
                capability_id="pytest_unit",
                state=ApplicabilityState.APPLICABLE,
                reason="All signals satisfied",
                evidence=["pyproject.toml"]
            ),
            ApplicabilityResult(
                capability_id="schemathesis_api",
                state=ApplicabilityState.NOT_APPLICABLE,
                reason="Missing required signals: openapi_spec",
                evidence=[]
            )
        ]

        scope = ProjectScope(types=["unit", "api"], risk_approval="high")
        profile = {"language": "python"}

        recommendations = engine.generate_recommendations(results, scope, profile)

        assert len(recommendations) == 1
        assert recommendations[0]["capability_id"] == "schemathesis_api"
        assert recommendations[0]["test_types"] == ["api"]
        assert "rationale" in recommendations[0]
        assert "prerequisites" in recommendations[0]

    def test_recommendations_sorted_by_risk(self):
        """Recommendations sorted by risk level (low first)."""
        from asta.capability import CapabilityRegistry, ApplicabilityResult, ApplicabilityState

        registry = CapabilityRegistry()
        engine = RecommendationEngine(registry)

        results = [
            ApplicabilityResult(capability_id="cap_high", state=ApplicabilityState.NOT_APPLICABLE, reason="", evidence=[]),
            ApplicabilityResult(capability_id="cap_low", state=ApplicabilityState.NOT_APPLICABLE, reason="", evidence=[]),
            ApplicabilityResult(capability_id="cap_medium", state=ApplicabilityState.NOT_APPLICABLE, reason="", evidence=[]),
        ]

        # Mock capabilities with different risk levels
        registry.capabilities["cap_low"] = type('Cap', (), {"risk_level": "low", "name": "Low Risk", "description": "", "test_types": ["unit"], "prerequisites": []})()
        registry.capabilities["cap_medium"] = type('Cap', (), {"risk_level": "medium", "name": "Medium Risk", "description": "", "test_types": ["unit"], "prerequisites": []})()
        registry.capabilities["cap_high"] = type('Cap', (), {"risk_level": "high", "name": "High Risk", "description": "", "test_types": ["unit"], "prerequisites": []})()

        scope = ProjectScope(types=["unit"], risk_approval="high")
        profile = {}

        recommendations = engine.generate_recommendations(results, scope, profile)

        # Should be sorted: low, medium, high
        assert recommendations[0]["capability_id"] == "cap_low"
        assert recommendations[1]["capability_id"] == "cap_medium"
        assert recommendations[2]["capability_id"] == "cap_high"


class TestPlanSerialization:
    """Test plan serialization."""

    def test_plan_to_dict(self):
        """Plan serializes to dict."""
        checks = [
            PlanCheck(key="check1", title="Check 1", description="", capability_id="c1", test_type="unit", state="included", reason="", risk_level="low")
        ]

        provenance = PlanProvenance(
            generated_at="2026-11-23T00:00:00Z",
            plan_revision=1,
            scope_types=["unit"],
            content_hash="hash"
        )

        plan = Plan(
            project_name="test",
            plan_revision=1,
            content_hash="hash",
            generated_at="2026-11-23T00:00:00Z",
            scope_types=["unit"],
            risk_approval="high",
            checks=checks,
            provenance=provenance
        )

        data = plan.to_dict()

        assert data["project_name"] == "test"
        assert data["plan_revision"] == 1
        assert data["content_hash"] == "hash"
        assert len(data["checks"]) == 1
        assert data["checks"][0]["key"] == "check1"
        assert data["provenance"]["ai_off"] == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])