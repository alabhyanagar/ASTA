#!/usr/bin/env python3
"""
ASTA M1 Language Boundary Tests
"""

import pytest
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from asta.language_boundary import (
    LanguageBoundaryEngine, LanguageBoundary, TestLanguage, TargetType,
    LanguageBinding, LanguageCompatibility, BoundaryDeclaration,
    BoundaryDeclarationManager, M1_SUPPORTED_TEST_LANGUAGES,
    M1_SUPPORTED_TARGET_LANGUAGES, LANGUAGE_COMPATIBILITY_MATRIX,
    LanguageBoundaryEngine, integrate_language_boundaries
)
from asta.capability import CapabilityRegistry
from asta.planner import CheckState
from asta.models import ProjectScope


class TestLanguageBoundaryEnums:
    """Test language boundary enums."""

    def test_language_boundary_values(self):
        assert LanguageBoundary.WHITE_BOX.value == "white_box"
        assert LanguageBoundary.BLACK_BOX.value == "black_box"
        assert LanguageBoundary.HYBRID.value == "hybrid"

    def test_test_language_values(self):
        assert TestLanguage.PYTHON.value == "python"
        assert TestLanguage.JAVASCRIPT.value == "javascript"
        assert TestLanguage.GO.value == "go"

    def test_target_type_values(self):
        assert TargetType.SOURCE_CODE.value == "source_code"
        assert TargetType.API_ENDPOINT.value == "api_endpoint"
        assert TargetType.RUNNING_SERVICE.value == "running_service"


class TestLanguageBinding:
    """Test LanguageBinding data structure."""

    def test_binding_creation(self):
        """Create language binding."""
        binding = LanguageBinding(
            check_key="pytest_unit_binding",
            capability_id="pytest_unit",
            test_language=TestLanguage.PYTHON,
            target_language=TestLanguage.PYTHON,
            target_type=TargetType.SOURCE_CODE,
            boundary=LanguageBoundary.WHITE_BOX,
            requires_same_runtime=True,
            runtime_ecosystem="pytest",
            binding_declared=False,
            declaration_source="capability"
        )

        assert binding.check_key == "pytest_unit_binding"
        assert binding.capability_id == "pytest_unit"
        assert binding.test_language == TestLanguage.PYTHON
        assert binding.target_language == TestLanguage.PYTHON
        assert binding.boundary == LanguageBoundary.WHITE_BOX
        assert binding.requires_same_runtime == True
        assert binding.runtime_ecosystem == "pytest"

    def test_binding_to_dict(self):
        """Binding serializes to dict."""
        binding = LanguageBinding(
            check_key="test", capability_id="cap1",
            test_language=TestLanguage.PYTHON,
            target_language=TestLanguage.PYTHON,
            target_type=TargetType.SOURCE_CODE,
            boundary=LanguageBoundary.WHITE_BOX
        )

        data = binding.to_dict()

        assert data["check_key"] == "test"
        assert data["capability_id"] == "cap1"
        assert data["boundary"] == "white_box"
        assert data["test_language"] == "python"
        assert data["target_language"] == "python"


class TestLanguageBoundaryEngine:
    """Test LanguageBoundaryEngine."""

    def setup_method(self):
        self.registry = CapabilityRegistry()
        self.engine = LanguageBoundaryEngine()

    def test_determine_binding_pytest_unit(self):
        """Determine binding for pytest_unit (white-box)."""
        binding = self.engine.determine_binding(
            capability_id="pytest_unit",
            project_profile={"language": "python"},
            capability_registry=self.registry,
            project_scope={"types": ["unit"]}
        )

        assert binding.capability_id == "pytest_unit"
        assert binding.boundary == LanguageBoundary.WHITE_BOX
        assert binding.test_language == TestLanguage.PYTHON
        assert binding.target_language == TestLanguage.PYTHON
        assert binding.target_type == TargetType.SOURCE_CODE
        assert binding.requires_same_runtime == True
        assert binding.runtime_ecosystem == "pytest"
        assert binding.binding_declared == False  # Not required for unit
        assert binding.declaration_source == "capability"

    def test_determine_binding_schemathesis_api(self):
        """Determine binding for schemathesis_api (black-box)."""
        binding = self.engine.determine_binding(
            capability_id="schemathesis_api",
            project_profile={"language": "python"},
            capability_registry=self.registry,
            project_scope={"types": ["api"]}
        )

        assert binding.capability_id == "schemathesis_api"
        assert binding.boundary == LanguageBoundary.BLACK_BOX
        assert binding.test_language == TestLanguage.PYTHON
        assert binding.target_language == TestLanguage.PYTHON
        assert binding.target_type == TargetType.API_ENDPOINT
        assert binding.requires_same_runtime == False
        assert binding.runtime_ecosystem == "schemathesis"
        assert binding.binding_declared == False  # Black-box doesn't require declaration

    def test_determine_binding_httpx_api_assert(self):
        """Determine binding for httpx_api_assert (black-box)."""
        binding = self.engine.determine_binding(
            capability_id="httpx_api_assert",
            project_profile={"language": "python"},
            capability_registry=self.registry,
            project_scope={"types": ["api"]}
        )

        assert binding.boundary == LanguageBoundary.BLACK_BOX
        assert binding.target_type == TargetType.API_ENDPOINT
        assert binding.runtime_ecosystem == "httpx"

    def test_determine_binding_pytest_integration(self):
        """Determine binding for pytest_integration (white-box, requires declaration)."""
        binding = self.engine.determine_binding(
            capability_id="pytest_integration",
            project_profile={"language": "python"},
            capability_registry=self.registry,
            project_scope={"types": ["integration"]}
        )

        assert binding.boundary == LanguageBoundary.WHITE_BOX
        assert binding.target_type == TargetType.SOURCE_CODE
        assert binding.binding_declared == True  # Integration requires declaration
        assert binding.declaration_source == "plan"
        assert binding.runtime_ecosystem == "pytest"

    def test_validate_binding_white_box_valid(self):
        """Validate valid white-box binding."""
        from asta.capability import CapabilityRegistry

        registry = CapabilityRegistry()
        engine = LanguageBoundaryEngine()

        binding = engine.determine_binding(
            capability_id="pytest_unit",
            project_profile={"language": "python"},
            capability_registry=registry,
            project_scope={"types": ["unit"]}
        )

        valid, reason = engine.validate_binding(binding, {"language": "python"})

        assert valid == True
        assert reason == "Valid"

    def test_validate_binding_black_box_valid(self):
        """Validate valid black-box binding."""
        from asta.capability import CapabilityRegistry

        registry = CapabilityRegistry()
        engine = LanguageBoundaryEngine()

        binding = engine.determine_binding(
            capability_id="schemathesis_api",
            project_profile={"language": "python"},
            capability_registry=registry,
            project_scope={"types": ["api"]}
        )

        valid, reason = engine.validate_binding(binding, {"language": "python"})

        assert valid == True
        assert reason == "Valid"

    def test_validate_binding_white_box_mismatch(self):
        """White-box binding invalid if languages don't match."""
        binding = LanguageBinding(
            check_key="test", capability_id="pytest_unit",
            test_language=TestLanguage.PYTHON,
            target_language=TestLanguage.JAVASCRIPT,  # Mismatch!
            target_type=TargetType.SOURCE_CODE,
            boundary=LanguageBoundary.WHITE_BOX,
            requires_same_runtime=True
        )

        engine = LanguageBoundaryEngine()
        valid, reason = engine.validate_binding(binding, {})

        assert valid == False
        assert "match" in reason.lower()

    def test_validate_binding_unsupported_test_language(self):
        """Binding invalid if test language not supported."""
        binding = LanguageBinding(
            check_key="test", capability_id="test",
            test_language=TestLanguage.RUBY,  # Not in M1
            target_language=TestLanguage.PYTHON,
            target_type=TargetType.SOURCE_CODE,
            boundary=LanguageBoundary.WHITE_BOX
        )

        engine = LanguageBoundaryEngine()
        valid, reason = engine.validate_binding(binding, {})

        assert valid == False
        assert "not supported" in reason.lower()

    def test_validate_binding_component_requires_declaration(self):
        """Component/integration binding invalid without declaration."""
        binding = LanguageBinding(
            check_key="test", capability_id="pytest_integration",
            test_language=TestLanguage.PYTHON,
            target_language=TestLanguage.PYTHON,
            target_type=TargetType.SOURCE_CODE,
            boundary=LanguageBoundary.WHITE_BOX,
            requires_same_runtime=True,
            binding_declared=True,
            declaration_source=""  # Empty!
        )

        engine = LanguageBoundaryEngine()
        valid, reason = engine.validate_binding(binding, {})

        assert valid == False
        assert "declaration" in reason.lower()

    def test_get_all_bindings(self):
        """Get all determined bindings."""
        from asta.capability import CapabilityRegistry

        registry = CapabilityRegistry()
        engine = LanguageBoundaryEngine()

        caps = ["pytest_unit", "pytest_integration", "schemathesis_api", "httpx_api_assert"]
        for cap_id in caps:
            engine.determine_binding(
                capability_id=cap_id,
                project_profile={"language": "python"},
                capability_registry=registry,
                project_scope={"types": ["unit", "integration", "api"]}
            )

        bindings = engine.get_all_bindings()
        assert len(bindings) == 4


class TestBoundaryDeclaration:
    """Test boundary declarations."""

    def test_declaration_creation(self):
        """Create boundary declaration."""
        decl = BoundaryDeclaration(
            check_key="pytest_integration",
            capability_id="pytest_integration",
            boundary=LanguageBoundary.WHITE_BOX,
            test_language=TestLanguage.PYTHON,
            target_language=TestLanguage.PYTHON,
            target_type=TargetType.SOURCE_CODE,
            declared_by="user",
            runtime_ecosystem="pytest",
            notes="Integration tests require pytest"
        )

        assert decl.check_key == "pytest_integration"
        assert decl.boundary == LanguageBoundary.WHITE_BOX
        assert decl.declared_by == "user"
        assert decl.runtime_ecosystem == "pytest"

    def test_declaration_to_dict(self):
        """Declaration serializes to dict."""
        decl = BoundaryDeclaration(
            check_key="test", capability_id="cap1",
            boundary=LanguageBoundary.WHITE_BOX,
            test_language=TestLanguage.PYTHON,
            target_language=TestLanguage.PYTHON,
            target_type=TargetType.SOURCE_CODE,
            declared_by="user"
        )

        data = decl.to_dict()

        assert data["check_key"] == "test"
        assert data["boundary"] == "white_box"
        assert data["declared_by"] == "user"
        assert data["test_language"] == "python"


class TestBoundaryDeclarationManager:
    """Test BoundaryDeclarationManager."""

    def setup_method(self):
        self.manager = BoundaryDeclarationManager()

    def test_declare_and_get(self):
        """Declare and retrieve boundary declaration."""
        decl = BoundaryDeclaration(
            check_key="pytest_integration",
            capability_id="pytest_integration",
            boundary=LanguageBoundary.WHITE_BOX,
            test_language=TestLanguage.PYTHON,
            target_language=TestLanguage.PYTHON,
            target_type=TargetType.SOURCE_CODE,
            declared_by="user",
            runtime_ecosystem="pytest"
        )

        self.manager.declare(decl)

        retrieved = self.manager.get("pytest_integration")
        assert retrieved is not None
        assert retrieved.check_key == "pytest_integration"
        assert retrieved.boundary == LanguageBoundary.WHITE_BOX

    def test_has_declaration(self):
        """Check if declaration exists."""
        decl = BoundaryDeclaration(
            check_key="test", capability_id="cap1",
            boundary=LanguageBoundary.WHITE_BOX,
            test_language=TestLanguage.PYTHON,
            target_language=TestLanguage.PYTHON,
            target_type=TargetType.SOURCE_CODE,
            declared_by="user"
        )

        assert self.manager.has_declaration("test") == False

        self.manager.declare(decl)
        assert self.manager.has_declaration("test") == True

    def test_validate_declaration_valid(self):
        """Validate valid declaration."""
        decl = BoundaryDeclaration(
            check_key="test", capability_id="cap1",
            boundary=LanguageBoundary.WHITE_BOX,
            test_language=TestLanguage.PYTHON,
            target_language=TestLanguage.PYTHON,
            target_type=TargetType.SOURCE_CODE,
            declared_by="user",
            runtime_ecosystem="pytest"
        )

        valid, reason = self.manager.validate_declaration(decl, {"language": "python"})

        assert valid == True
        assert reason == "Valid"

    def test_validate_declaration_invalid_language(self):
        """Invalid declaration for unsupported language."""
        decl = BoundaryDeclaration(
            check_key="test", capability_id="cap1",
            boundary=LanguageBoundary.WHITE_BOX,
            test_language=TestLanguage.RUBY,  # Not supported
            target_language=TestLanguage.PYTHON,
            target_type=TargetType.SOURCE_CODE,
            declared_by="user"
        )

        valid, reason = self.manager.validate_declaration(decl, {})

        assert valid == False
        assert "not supported" in reason.lower()

    def test_validate_declaration_mismatch(self):
        """Invalid declaration: white-box with mismatched languages."""
        decl = BoundaryDeclaration(
            check_key="test", capability_id="cap1",
            boundary=LanguageBoundary.WHITE_BOX,
            test_language=TestLanguage.PYTHON,
            target_language=TestLanguage.JAVASCRIPT,  # Mismatch
            target_type=TargetType.SOURCE_CODE,
            declared_by="user"
        )

        valid, reason = self.manager.validate_declaration(decl, {})

        assert valid == False
        assert "match" in reason.lower()


class TestLanguageCompatibilityMatrix:
    """Test language compatibility matrix."""

    def test_python_compatibility(self):
        """Python compatibility settings."""
        compat = LANGUAGE_COMPATIBILITY_MATRIX[TestLanguage.PYTHON]

        assert compat.test_language == TestLanguage.PYTHON
        assert TestLanguage.PYTHON in compat.compatible_target_languages
        assert "pytest" in compat.compatible_runtimes
        assert compat.white_box_supported == True
        assert compat.black_box_supported == True

    def test_javascript_compatibility(self):
        """JavaScript compatibility settings."""
        compat = LANGUAGE_COMPATIBILITY_MATRIX[TestLanguage.JAVASCRIPT]

        assert TestLanguage.JAVASCRIPT in compat.compatible_target_languages
        assert TestLanguage.TYPESCRIPT in compat.compatible_target_languages
        assert "jest" in compat.compatible_runtimes
        assert "mocha" in compat.compatible_runtimes

    def test_m1_supported_languages(self):
        """M1 supported languages list."""
        assert TestLanguage.PYTHON in M1_SUPPORTED_TEST_LANGUAGES
        assert TestLanguage.PYTHON in M1_SUPPORTED_TARGET_LANGUAGES
        assert len(M1_SUPPORTED_TEST_LANGUAGES) == 1  # Only Python in M1


class TestPlanIntegration:
    """Test language boundary integration with plans."""

    def test_integrate_language_boundaries(self):
        """Integrate language boundaries into plan."""
        from asta.planner import Plan, PlanProvenance, PlanCheck, CheckState
        from asta.capability import CapabilityRegistry
        from asta.models import ProjectScope

        plan = Plan(
            project_name="test", plan_revision=1, content_hash="hash",
            generated_at="2026-11-23T00:00:00Z", scope_types=["unit", "api"], risk_approval="high",
            checks=[
                PlanCheck(key="c1", title="Pytest Unit", description="", capability_id="pytest_unit",
                         test_type="unit", state=CheckState.INCLUDED, reason="", risk_level="low"),
                PlanCheck(key="c2", title="Schemathesis API", description="", capability_id="schemathesis_api",
                         test_type="api", state=CheckState.INCLUDED, reason="", risk_level="medium")
            ],
            provenance=PlanProvenance(generated_at="2026-11-23T00:00:00Z", plan_revision=1,
                                    scope_types=["unit", "api"], content_hash="hash", policy_version="1.0")
        )

        engine = LanguageBoundaryEngine()
        registry = CapabilityRegistry()
        scope = ProjectScope(types=["unit", "api"], risk_approval="high")

        # This would need a full project profile
        project_profile = {"language": "python"}

        # Test that integration adds language binding to checks
        result_plan = integrate_language_boundaries(
            plan=plan,
            engine=engine,
            project_profile={"language": "python"},
            capability_registry=registry,
            project_scope=scope
        )

        # Check that language bindings were added
        for check in result_plan.checks:
            if check.capability_id in ["pytest_unit", "schemathesis_api"]:
                assert "language_binding" in check.limits
                binding = check.limits["language_binding"]
                assert "boundary" in binding
                assert "test_language" in binding
                assert "target_language" in binding


if __name__ == "__main__":
    pytest.main([__file__, "-v"])