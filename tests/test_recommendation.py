#!/usr/bin/env python3
"""
ASTA M1 Recommendation Tests
"""

import pytest
import json
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from asta.recommendation import (
    RecommendationManager, ApprovalBindingManager, RecommendationReviewWorkflow,
    Recommendation, ApprovalBinding, RecommendationStatus, RecommendationType
)
from asta.planner import Plan, PlanCheck, CheckState, PlanProvenance
from asta.capability import CapabilityRegistry, Capability
from asta.models import ProjectScope


class TestRecommendation:
    """Test Recommendation data structure."""

    def test_recommendation_creation(self):
        """Create recommendation with all fields."""
        rec = Recommendation(
            recommendation_id="rec_test123",
            type="additional_check",
            capability_id="schemathesis_api",
            title="API Contract Testing (Schemathesis)",
            description="Generate and execute API tests from OpenAPI spec",
            rationale="Provides API contract coverage",
            evidence=["openapi.yaml"],
            risk_level="medium",
            prerequisites=["schemathesis>=5.6.0"],
            estimated_effort="medium",
            test_types=["api"]
        )

        assert rec.recommendation_id == "rec_test123"
        assert rec.type == "additional_check"
        assert rec.capability_id == "schemathesis_api"
        assert rec.status == "pending"
        assert rec.created_at is not None

    def test_recommendation_to_dict(self):
        """Recommendation serializes to dict."""
        rec = Recommendation(
            recommendation_id="rec_test",
            type="additional_check",
            capability_id="cap1",
            title="Test Rec",
            description="Desc",
            rationale="Rationale",
            risk_level="low"
        )

        data = rec.to_dict()

        assert data["recommendation_id"] == "rec_test"
        assert data["type"] == "additional_check"
        assert data["capability_id"] == "cap1"
        assert data["status"] == "pending"
        assert data["risk_level"] == "low"


class TestApprovalBinding:
    """Test ApprovalBinding data structure."""

    def test_binding_creation(self):
        """Create approval binding."""
        binding = ApprovalBinding(
            binding_id="bind_test123",
            plan_content_hash="abc123",
            plan_revision=1,
            project_name="test-project",
            scope_types=["unit", "integration"],
            risk_approval="high",
            policy_version="1.0",
            approved_checks=["check1", "check2"],
            excluded_checks=["check3"],
            approved_recommendations=["rec1"],
            declined_recommendations=["rec2"],
            deferred_recommendations=["rec3"],
            approved_by="user1"
        )

        assert binding.binding_id == "bind_test123"
        assert binding.valid == True
        assert binding.invalidation_reason is None
        assert binding.approved_by == "user1"

    def test_binding_to_dict(self):
        """Binding serializes to dict."""
        binding = ApprovalBinding(
            binding_id="bind_test",
            plan_content_hash="hash",
            plan_revision=1,
            project_name="test",
            scope_types=["unit"],
            risk_approval="high",
            policy_version="1.0",
            approved_by="user1"
        )

        data = binding.to_dict()

        assert data["binding_id"] == "bind_test"
        assert data["valid"] == True
        assert data["approved_by"] == "user1"


class TestRecommendationManager:
    """Test RecommendationManager."""

    def setup_method(self):
        self.registry = CapabilityRegistry()
        self.manager = RecommendationManager(self.registry)
        self.scope = ProjectScope(types=["unit", "integration", "api"], risk_approval="high")
        self.profile = {"language": "python"}

    def test_create_recommendations_from_not_applicable(self):
        """Create recommendations from NOT_APPLICABLE checks."""
        from asta.planner import PlanCheck, CheckState

        # Create checks with NOT_APPLICABLE state
        checks = [
            PlanCheck(
                key="check1", title="Pytest Unit", description="", capability_id="pytest_unit",
                test_type="unit", state="included", reason="", risk_level="low"
            ),
            PlanCheck(
                key="check2", title="Schemathesis API", description="", capability_id="schemathesis_api",
                test_type="api", state="not_applicable", reason="Missing OpenAPI spec", risk_level="medium"
            ),
            PlanCheck(
                key="check3", title="HTTPX API Assert", description="", capability_id="httpx_api_assert",
                test_type="api", state="unsupported", reason="No authorized target", risk_level="low"
            )
        ]

        recommendations = self.manager.create_recommendations(
            plan_checks=checks,
            capability_registry=self.registry,
            project_scope=self.scope,
            project_profile={"language": "python"}
        )

        # Should create recommendations for schemathesis_api and httpx_api_assert
        # (not for pytest_unit which is INCLUDED)
        assert len(recommendations) == 2

        rec_ids = {r.capability_id for r in recommendations}
        assert "schemathesis_api" in rec_ids
        assert "httpx_api_assert" in rec_ids
        assert "pytest_unit" not in rec_ids

    def test_recommendation_has_required_fields(self):
        """Recommendations have all required fields."""
        from asta.planner import PlanCheck, CheckState

        checks = [
            PlanCheck(
                key="check1", title="Schemathesis API", description="", capability_id="schemathesis_api",
                test_type="api", state="not_applicable", reason="Missing OpenAPI spec", risk_level="medium"
            )
        ]

        recommendations = self.manager.create_recommendations(
            plan_checks=checks,
            capability_registry=self.registry,
            project_scope=self.scope,
            project_profile={"language": "python"}
        )

        rec = recommendations[0]
        assert rec.recommendation_id.startswith("rec_")
        assert rec.type == "additional_check"
        assert rec.capability_id == "schemathesis_api"
        assert rec.title == "API Contract Testing (Schemathesis)"
        assert "coverage" in rec.rationale or "rationale" in rec.rationale
        assert rec.risk_level == "medium"
        assert "schemathesis" in rec.prerequisites[0].lower()
        assert rec.estimated_effort in ["low", "medium", "high"]
        assert rec.test_types == ["api"]
        assert rec.status == "pending"

    def test_review_recommendation(self):
        """Review recommendation with decision."""
        from asta.planner import PlanCheck, CheckState

        checks = [
            PlanCheck(key="check1", title="Test", description="", capability_id="pytest_unit",
                     test_type="unit", state="not_applicable", reason="", risk_level="low")
        ]

        self.manager.create_recommendations(
            plan_checks=checks,
            capability_registry=self.registry,
            project_scope=self.scope,
            project_profile={}
        )

        rec_id = list(self.manager.recommendations.keys())[0]

        # Approve
        result = self.manager.review_recommendation(rec_id, "approved", "user1")
        assert result == True

        rec = self.manager.recommendations[rec_id]
        assert rec.status == "approved"
        assert rec.reviewed_by == "user1"
        assert rec.review_decision == "approved"
        assert rec.reviewed_at is not None

        # Decline another
        checks2 = [type('Check', (), {
            'key': 'check2', 'title': 'Test2', 'description': '', 'capability_id': 'pytest_integration',
            'test_type': 'integration', 'state': 'not_applicable', 'reason': '', 'risk_level': 'low'
        })()]

        self.manager.create_recommendations(
            plan_checks=checks2,
            capability_registry=self.registry,
            project_scope=self.scope,
            project_profile={}
        )

        rec_id2 = [k for k in self.manager.recommendations.keys() if k != rec_id][0]
        result = self.manager.review_recommendation(rec_id2, "declined", "user1", "Not needed")
        assert result == True

        rec2 = self.manager.recommendations[rec_id2]
        assert rec2.status == "declined"
        assert rec2.review_decision == "declined"

    def test_get_approved_declined(self):
        """Get approved and declined recommendations."""
        from asta.planner import PlanCheck, CheckState

        checks = [
            PlanCheck(key="c1", title="Cap1", description="", capability_id="pytest_unit",
                     test_type="unit", state="not_applicable", reason="", risk_level="low"),
            PlanCheck(key="c2", title="Cap2", description="", capability_id="pytest_integration",
                     test_type="integration", state="not_applicable", reason="", risk_level="low"),
            PlanCheck(key="c3", title="Cap3", description="", capability_id="schemathesis_api",
                     test_type="api", state="not_applicable", reason="", risk_level="low")
        ]

        self.manager.create_recommendations(
            plan_checks=checks,
            capability_registry=self.registry,
            project_scope=self.scope,
            project_profile={}
        )

        rec_ids = list(self.manager.recommendations.keys())

        # Approve first, decline second, defer third
        self.manager.review_recommendation(rec_ids[0], "approved", "user1")
        self.manager.review_recommendation(rec_ids[1], "declined", "user1")
        self.manager.review_recommendation(rec_ids[2], "deferred", "user1")

        approved = self.manager.get_approved_recommendations()
        declined = self.manager.get_declined_recommendations()

        assert len(approved) == 1
        assert len(declined) == 1
        assert self.manager.recommendations[rec_ids[2]].status == "deferred"


class TestApprovalBindingManager:
    """Test ApprovalBindingManager."""

    def setup_method(self):
        self.manager = ApprovalBindingManager()

    def test_create_binding(self):
        """Create approval binding."""
        from asta.planner import Plan, PlanProvenance, PlanCheck, CheckState

        plan = Plan(
            project_name="test", plan_revision=1, content_hash="abc123",
            generated_at="2026-11-23T00:00:00Z", scope_types=["unit"], risk_approval="high",
            checks=[PlanCheck(key="c1", title="C1", description="", capability_id="cap1",
                             test_type="unit", state="included", reason="", risk_level="low")],
            provenance=PlanProvenance(generated_at="2026-11-23T00:00:00Z", plan_revision=1,
                                    scope_types=["unit"], content_hash="abc123", policy_version="1.0")
        )

        binding = self.manager.create_binding(
            plan=plan,
            project_name="test-project",
            scope_types=["unit"],
            risk_approval="high",
            approved_checks=["check1"],
            excluded_checks=[],
            approved_recommendations=["rec1"],
            declined_recommendations=["rec2"],
            deferred_recommendations=["rec3"],
            approved_by="user1"
        )

        assert binding.binding_id.startswith("bind_")
        assert binding.plan_content_hash == "abc123"
        assert binding.plan_revision == 1
        assert binding.project_name == "test-project"
        assert binding.approved_by == "user1"
        assert binding.valid == True

    def test_validate_binding_valid(self):
        """Validate binding against matching plan."""
        from asta.planner import Plan, PlanProvenance, PlanCheck, CheckState

        plan = Plan(
            project_name="test", plan_revision=1, content_hash="hash123",
            generated_at="2026-11-23T00:00:00Z", scope_types=["unit"], risk_approval="high",
            checks=[], provenance=PlanProvenance(generated_at="2026-11-23T00:00:00Z", plan_revision=1,
                                                scope_types=["unit"], content_hash="hash123", policy_version="1.0")
        )

        binding = ApprovalBinding(
            binding_id="bind1", plan_content_hash="hash123", plan_revision=1,
            project_name="test", scope_types=["unit"], risk_approval="high",
            policy_version="1.0", approved_by="user1"
        )

        valid, reason = ApprovalBindingManager().validate_binding(binding, plan)
        assert valid == True
        assert reason == "Valid"

    def test_validate_binding_invalid_hash(self):
        """Binding invalid when plan content hash differs."""
        from asta.planner import Plan, PlanProvenance

        plan = Plan(project_name="test", plan_revision=1, content_hash="different_hash",
                   generated_at="2026-11-23T00:00:00Z", scope_types=["unit"], risk_approval="high",
                   checks=[], provenance=PlanProvenance(generated_at="2026-11-23T00:00:00Z",
                                                      plan_revision=1, scope_types=["unit"],
                                                      content_hash="different_hash", policy_version="1.0"))

        binding = ApprovalBinding(
            binding_id="bind1", plan_content_hash="hash123", plan_revision=1,
            project_name="test", scope_types=["unit"], risk_approval="high",
            policy_version="1.0", approved_by="user1"
        )

        valid, reason = ApprovalBindingManager().validate_binding(binding, plan)
        assert valid == False
        assert "content hash changed" in reason.lower()

    def test_validate_binding_invalid_revision(self):
        """Binding invalid when plan revision differs."""
        from asta.planner import Plan, PlanProvenance

        plan = Plan(project_name="test", plan_revision=2, content_hash="hash123",
                   generated_at="2026-11-23T00:00:00Z", scope_types=["unit"], risk_approval="high",
                   checks=[], provenance=PlanProvenance(generated_at="2026-11-23T00:00:00Z",
                                                      plan_revision=2, scope_types=["unit"],
                                                      content_hash="hash123", policy_version="1.0"))

        binding = ApprovalBinding(
            binding_id="bind1", plan_content_hash="hash123", plan_revision=1,
            project_name="test", scope_types=["unit"], risk_approval="high",
            policy_version="1.0", approved_by="user1"
        )

        valid, reason = ApprovalBindingManager().validate_binding(binding, plan)
        assert valid == False
        assert "revision changed" in reason.lower()

    def test_invalidate_binding(self):
        """Invalidate binding with reason."""
        binding = ApprovalBinding(
            binding_id="bind1", plan_content_hash="hash", plan_revision=1,
            project_name="test", scope_types=["unit"], risk_approval="high",
            policy_version="1.0", approved_by="user1"
        )

        manager = ApprovalBindingManager()
        manager.bindings["bind1"] = binding

        result = manager.invalidate_binding("bind1", "Material plan change")
        assert result == True

        binding = manager.bindings["bind1"]
        assert binding.valid == False
        assert binding.invalidation_reason == "Material plan change"
        assert binding.invalidated_at is not None

    def test_check_and_invalidate_on_change(self):
        """Check and invalidate on material plan change."""
        from asta.planner import Plan, PlanProvenance, PlanCheck, CheckState, PlanChangeDetector

        old_plan = Plan(
            project_name="test", plan_revision=1, content_hash="hash1",
            generated_at="2026-11-23T00:00:00Z", scope_types=["unit"], risk_approval="high",
            checks=[PlanCheck(key="c1", title="C1", description="", capability_id="cap1",
                             test_type="unit", state="included", reason="", risk_level="low")],
            provenance=PlanProvenance(generated_at="2026-11-23T00:00:00Z", plan_revision=1,
                                    scope_types=["unit"], content_hash="hash1", policy_version="1.0")
        )

        new_plan = Plan(
            project_name="test", plan_revision=2, content_hash="hash2",
            generated_at="2026-11-23T00:00:00Z", scope_types=["unit", "integration"], risk_approval="high",
            checks=[
                PlanCheck(key="c1", title="C1", description="", capability_id="cap1",
                         test_type="unit", state="included", reason="", risk_level="low"),
                PlanCheck(key="c2", title="C2", description="", capability_id="cap2",
                         test_type="integration", state="included", reason="", risk_level="medium")
            ],
            provenance=PlanProvenance(generated_at="2026-11-23T00:00:00Z", plan_revision=2,
                                    scope_types=["unit", "integration"], content_hash="hash2", policy_version="1.0")
        )

        binding = ApprovalBinding(
            binding_id="bind1", plan_content_hash="hash1", plan_revision=1,
            project_name="test", scope_types=["unit"], risk_approval="high",
            policy_version="1.0", approved_by="user1"
        )

        manager = ApprovalBindingManager()
        manager.bindings["bind1"] = binding

        invalidated, reason = manager.check_and_invalidate_on_change("bind1", old_plan, new_plan)

        assert invalidated == True
        assert "material change" in reason.lower()

        binding = manager.bindings["bind1"]
        assert binding.valid == False


class TestRecommendationReviewWorkflow:
    """Test RecommendationReviewWorkflow."""

    def setup_method(self):
        self.registry = CapabilityRegistry()
        with tempfile.TemporaryDirectory() as tmpdir:
            self.project_path = Path(tmpdir)

    def test_generate_recommendations_for_plan(self):
        """Generate recommendations for a plan."""
        from asta.planner import Plan, PlanProvenance, PlanCheck, CheckState

        plan = Plan(
            project_name="test", plan_revision=1, content_hash="hash",
            generated_at="2026-11-23T00:00:00Z", scope_types=["unit", "api"], risk_approval="high",
            checks=[
                PlanCheck(key="c1", title="Pytest Unit", description="", capability_id="pytest_unit",
                         test_type="unit", state="included", reason="", risk_level="low"),
                PlanCheck(key="c2", title="Schemathesis API", description="", capability_id="schemathesis_api",
                         test_type="api", state="not_applicable", reason="Missing OpenAPI spec", risk_level="medium")
            ],
            provenance=PlanProvenance(generated_at="2026-11-23T00:00:00Z", plan_revision=1,
                                    scope_types=["unit", "api"], content_hash="hash", policy_version="1.0")
        )

        workflow = RecommendationReviewWorkflow(self.registry, self.project_path)
        scope = ProjectScope(types=["unit", "api"], risk_approval="high")

        recommendations = workflow.generate_recommendations_for_plan(plan, scope, {"language": "python"})

        assert len(recommendations) == 1
        assert recommendations[0].capability_id == "schemathesis_api"
        assert recommendations[0].status == "pending"

    def test_create_approval_binding(self):
        """Create approval binding after review."""
        from asta.planner import Plan, PlanProvenance, PlanCheck, CheckState

        plan = Plan(
            project_name="test", plan_revision=1, content_hash="hash",
            generated_at="2026-11-23T00:00:00Z", scope_types=["unit", "api"], risk_approval="high",
            checks=[
                PlanCheck(key="c1", title="Pytest Unit", description="", capability_id="pytest_unit",
                         test_type="unit", state="included", reason="", risk_level="low"),
                PlanCheck(key="c2", title="Schemathesis API", description="", capability_id="schemathesis_api",
                         test_type="api", state="not_applicable", reason="Missing OpenAPI spec", risk_level="medium")
            ],
            provenance=PlanProvenance(generated_at="2026-11-23T00:00:00Z", plan_revision=1,
                                    scope_types=["unit", "api"], content_hash="hash", policy_version="1.0")
        )

        workflow = RecommendationReviewWorkflow(self.registry, self.project_path)
        scope = ProjectScope(types=["unit", "api"], risk_approval="high")

        # Generate and approve recommendation
        workflow.generate_recommendations_for_plan(plan, scope, {"language": "python"})
        rec_id = list(workflow.rec_manager.recommendations.keys())[0]
        workflow.rec_manager.review_recommendation(rec_id, "approved", "user1")

        # Create binding
        binding = workflow.create_approval_binding(
            plan=plan, project_name="test-project", scope_types=["unit", "api"], risk_approval="high",
            approved_checks=["pytest_unit"], excluded_checks=[], reviewer="user1"
        )

        assert binding.binding_id.startswith("bind_")
        assert binding.project_name == "test-project"
        assert binding.approved_by == "user1"
        assert len(binding.approved_recommendations) == 1

    def test_validate_existing_binding(self):
        """Validate existing binding against current plan."""
        from asta.planner import Plan, PlanProvenance, PlanCheck, CheckState

        workflow = RecommendationReviewWorkflow(self.registry, self.project_path)
        scope = ProjectScope(types=["unit"], risk_approval="high")

        plan = Plan(
            project_name="test", plan_revision=1, content_hash="hash1",
            generated_at="2026-11-23T00:00:00Z", scope_types=["unit"], risk_approval="high",
            checks=[PlanCheck(key="c1", title="Pytest Unit", description="", capability_id="pytest_unit",
                             test_type="unit", state="included", reason="", risk_level="low")],
            provenance=PlanProvenance(generated_at="2026-11-23T00:00:00Z", plan_revision=1,
                                    scope_types=["unit"], content_hash="hash1", policy_version="1.0")
        )

        # Create initial binding
        binding = workflow.binding_manager.create_binding(
            plan=plan, project_name="test-project", scope_types=["unit"], risk_approval="high",
            approved_checks=["pytest_unit"], excluded_checks=[], approved_recommendations=[],
            declined_recommendations=[], deferred_recommendations=[], approved_by="user1"
        )

        # Validate same plan
        valid, reason = workflow.validate_existing_binding(plan, "test-project")
        assert valid == True
        assert reason == "Valid"

        # Validate different plan
        plan2 = Plan(project_name="test", plan_revision=2, content_hash="hash2",
                    generated_at="2026-11-23T00:00:00Z", scope_types=["unit"], risk_approval="high",
                    checks=[], provenance=PlanProvenance(generated_at="2026-11-23T00:00:00Z",
                                                       plan_revision=2, scope_types=["unit"],
                                                       content_hash="hash2", policy_version="1.0"))

        valid, reason = workflow.validate_existing_binding(plan2, "test-project")
        assert valid == False
        assert "content hash changed" in reason.lower()

    def test_get_audit_trail(self):
        """Get complete audit trail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            registry = CapabilityRegistry()
            workflow = RecommendationReviewWorkflow(registry, project_path)
            scope = ProjectScope(types=["unit", "api"], risk_approval="high")

            from asta.planner import Plan, PlanProvenance, PlanCheck, CheckState

            plan = Plan(
                project_name="test", plan_revision=1, content_hash="hash",
                generated_at="2026-11-23T00:00:00Z", scope_types=["unit", "api"], risk_approval="high",
                checks=[
                    PlanCheck(key="c1", title="Pytest Unit", description="", capability_id="pytest_unit",
                             test_type="unit", state="included", reason="", risk_level="low"),
                    PlanCheck(key="c2", title="Schemathesis API", description="", capability_id="schemathesis_api",
                             test_type="api", state="not_applicable", reason="Missing OpenAPI spec", risk_level="medium")
                ],
                provenance=PlanProvenance(generated_at="2026-11-23T00:00:00Z", plan_revision=1,
                                        scope_types=["unit", "api"], content_hash="hash", policy_version="1.0")
            )

            workflow.generate_recommendations_for_plan(plan, scope, {})
            rec_id = list(workflow.rec_manager.recommendations.keys())[0]
            workflow.rec_manager.review_recommendation(rec_id, "approved", "user1")

            workflow.create_approval_binding(
                plan=plan, project_name="test-project", scope_types=["unit", "api"], risk_approval="high",
                approved_checks=["pytest_unit"], excluded_checks=[], reviewer="user1"
            )

            trail = workflow.get_audit_trail()

            # Should have recommendation + binding entries
            assert len(trail) >= 2

            rec_entry = next(e for e in trail if e["type"] == "recommendation")
            assert rec_entry["recommendation_id"] in workflow.rec_manager.recommendations
            assert rec_entry["status"] == "approved"

            bind_entry = next(e for e in trail if e["type"] == "approval_binding")
            assert bind_entry["binding_id"] is not None
            assert bind_entry["valid"] == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])