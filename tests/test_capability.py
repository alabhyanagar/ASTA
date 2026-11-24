#!/usr/bin/env python3
"""
ASTA M1 Pytest Tests for Capability Module
"""

import pytest
import json
import tempfile
from pathlib import Path
import sys
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).parent.parent))

from asta.capability import (
    CapabilityRegistry, ApplicabilityEvaluator, ApplicabilityResult,
    ApplicabilityState, Capability, CapabilitySignal,
    evaluate_all_capabilities, get_applicable_capabilities, get_capability_states
)


class TestCapabilityRegistry:
    """Test the capability registry."""

    def test_registry_has_builtin_capabilities(self):
        """Registry has M1 built-in capabilities."""
        registry = CapabilityRegistry()

        assert "pytest_unit" in registry.capabilities
        assert "pytest_integration" in registry.capabilities
        assert "schemathesis_api" in registry.capabilities
        assert "httpx_api_assert" in registry.capabilities

    def test_get_capability(self):
        """Get capability by ID."""
        registry = CapabilityRegistry()

        cap = registry.get("pytest_unit")
        assert cap is not None
        assert cap.capability_id == "pytest_unit"
        assert cap.name == "Python Unit Testing (pytest)"
        assert cap.adapter_id == "pytest_adapter"
        assert cap.test_types == ["unit"]
        assert cap.risk_level == "low"

    def test_list_by_test_type(self):
        """List capabilities by test type."""
        registry = CapabilityRegistry()

        unit_caps = registry.list_by_test_type("unit")
        assert len(unit_caps) == 1
        assert unit_caps[0].capability_id == "pytest_unit"

        api_caps = registry.list_by_test_type("api")
        assert len(api_caps) == 2
        assert {c.capability_id for c in api_caps} == {"schemathesis_api", "httpx_api_assert"}

        integration_caps = registry.list_by_test_type("integration")
        assert len(integration_caps) == 1
        assert integration_caps[0].capability_id == "pytest_integration"

    def test_list_by_adapter(self):
        """List capabilities by adapter."""
        registry = CapabilityRegistry()

        pytest_caps = registry.list_by_adapter("pytest_adapter")
        assert len(pytest_caps) == 2
        assert {c.capability_id for c in pytest_caps} == {"pytest_unit", "pytest_integration"}

        schemathesis_caps = registry.list_by_adapter("schemathesis_adapter")
        assert len(schemathesis_caps) == 1
        assert schemathesis_caps[0].capability_id == "schemathesis_api"

    def test_capability_signals(self):
        """Capability has required signals."""
        registry = CapabilityRegistry()
        cap = registry.get("pytest_unit")

        assert len(cap.signals) == 3
        signal_names = {s.name for s in cap.signals}
        assert "python_manifest" in signal_names
        assert "pytest_config" in signal_names
        assert "test_files" in signal_names

        # Check required flags
        required = [s.name for s in cap.signals if s.required]
        assert "python_manifest" in required
        assert "pytest_config" in required
        assert "test_files" in required

    def test_capability_unsupported_conditions(self):
        """Capability has unsupported conditions."""
        registry = CapabilityRegistry()
        cap = registry.get("pytest_unit")

        conditions = cap.unsupported_conditions
        assert "No Python project manifest found" in conditions
        assert "No pytest configuration found" in conditions
        assert "No test files found" in conditions


class TestApplicabilityEvaluator:
    """Test applicability evaluation."""

    def setup_method(self):
        self.registry = CapabilityRegistry()
        self.evaluator = ApplicabilityEvaluator(self.registry)
        self.scope = {"types": ["unit", "integration", "api"], "risk_approval": "high"}
        self.auth_manifest = {"allowed_targets": [], "authorized_risks": []}

    def create_python_project_facts(self) -> List[Dict]:
        """Create inspection facts for a typical Python project with pytest."""
        return [
            {"category": "language", "name": "python", "confidence": "high", "evidence": ["pyproject.toml"]},
            {"category": "language", "name": "primary", "value": "python", "confidence": "high", "evidence": []},
            {"category": "manifest", "name": "pyproject.toml", "confidence": "high", "evidence": ["Found pyproject.toml"]},
            {"category": "framework", "name": "pytest", "confidence": "high", "evidence": ["Found in pyproject.toml"]},
            {"category": "tool", "name": "pytest", "confidence": "high", "evidence": ["Found in pyproject.toml [tool.pytest]"]},
            {"category": "test_file", "name": "python test files", "value": "5", "confidence": "high", "evidence": ["Found 5 files matching test_*.py"]},
            {"category": "test_command", "name": "pytest", "confidence": "medium", "evidence": ["Inferred from pyproject.toml"]},
        ]

    def create_api_project_facts(self) -> List[Dict]:
        """Create inspection facts for an API project with OpenAPI spec."""
        return [
            {"category": "language", "name": "python", "confidence": "high", "evidence": ["pyproject.toml"]},
            {"category": "language", "name": "primary", "value": "python", "confidence": "high", "evidence": []},
            {"category": "manifest", "name": "pyproject.toml", "confidence": "high", "evidence": ["Found pyproject.toml"]},
            {"category": "api_spec", "name": "Sample API", "value": "OpenAPI 3.0.3", "confidence": "high", "evidence": ["Found openapi.yaml: Sample API v1.0.0"]},
            {"category": "deployment", "name": "docker", "confidence": "high", "evidence": ["Found Dockerfile"]},
        ]

    def create_empty_facts(self) -> List[Dict]:
        """Create empty facts for unknown project."""
        return []

    def test_pytest_unit_applicable(self):
        """pytest_unit applicable for Python project with pytest."""
        facts = self.create_python_project_facts()
        project_scope = {"types": ["unit"], "risk_approval": "low"}
        auth_manifest = {"allowed_targets": [], "authorized_risks": []}

        results = evaluate_all_capabilities(facts, project_scope, auth_manifest)

        pytest_result = next(r for r in results if r.capability_id == "pytest_unit")
        assert pytest_result.state == "Applicable"
        assert "All required signals satisfied" in pytest_result.reason

    def test_pytest_integration_applicable(self):
        """pytest_integration applicable with integration tests."""
        facts = self.create_python_project_facts()
        # Add integration test file
        facts.append({
            "category": "test_file",
            "name": "python integration test files",
            "value": "2",
            "confidence": "high",
            "evidence": ["Found 2 files matching *integration*.py"]
        })

        project_scope = {"types": ["integration"], "risk_approval": "medium"}
        auth_manifest = {"allowed_targets": [], "authorized_risks": ["medium"]}

        results = evaluate_all_capabilities(facts, project_scope, auth_manifest)

        pytest_result = next(r for r in results if r.capability_id == "pytest_integration")
        assert pytest_result.state == "Applicable"

    def test_schemathesis_api_applicable(self):
        """schemathesis_api applicable with OpenAPI spec and authorization."""
        facts = self.create_api_project_facts()
        project_scope = {"types": ["api"], "risk_approval": "medium"}
        auth_manifest = {"allowed_targets": ["https://api.example.com"], "authorized_risks": ["medium"]}

        results = evaluate_all_capabilities(facts, project_scope, auth_manifest)

        schemathesis_result = next(r for r in results if r.capability_id == "schemathesis_api")
        assert schemathesis_result.state == "Applicable"

    def test_schemathesis_api_not_applicable_no_spec(self):
        """schemathesis_api not applicable without OpenAPI spec."""
        facts = self.create_python_project_facts()  # No OpenAPI spec
        project_scope = {"types": ["api"], "risk_approval": "medium"}
        auth_manifest = {"allowed_targets": ["https://api.example.com"], "authorized_risks": ["medium"]}

        results = evaluate_all_capabilities(facts, project_scope, auth_manifest)

        schemathesis_result = next(r for r in results if r.capability_id == "schemathesis_api")
        assert schemathesis_result.state == "Not applicable"
        assert "Missing required signals" in schemathesis_result.reason
        assert "openapi_spec" in schemathesis_result.reason

    def test_medium_risk_no_auth_required(self):
        """Medium risk capabilities don't require explicit authorization."""
        facts = self.create_api_project_facts()
        project_scope = {"types": ["api"], "risk_approval": "medium"}
        auth_manifest = {"allowed_targets": ["https://api.example.com"], "authorized_risks": []}

        results = evaluate_all_capabilities(facts, project_scope, auth_manifest)

        schemathesis_result = next(r for r in results if r.capability_id == "schemathesis_api")
        assert schemathesis_result.state == "Applicable"
        assert "All required signals satisfied" in schemathesis_result.reason

    def test_high_risk_awaiting_authorization(self):
        """High risk capabilities require explicit authorization."""
        # Temporarily add a high-risk capability for testing
        from asta.capability import CapabilityRegistry, Capability, CapabilitySignal, evaluate_all_capabilities

        registry = CapabilityRegistry()
        registry.register(Capability(
            capability_id="test_high_risk",
            name="Test High Risk",
            description="Test capability with high risk",
            adapter_id="test_adapter",
            test_types=["api"],
            risk_level="high",
            signals=[
                CapabilitySignal(
                    name="openapi_spec",
                    category="api_spec",
                    required=True,
                    description="OpenAPI spec"
                ),
                CapabilitySignal(
                    name="api_target_authorized",
                    category="authorization",
                    required=True,
                    description="API target authorized"
                )
            ],
            prerequisites=[]
        ))

        facts = self.create_api_project_facts()
        project_scope = {"types": ["api"], "risk_approval": "high"}
        auth_manifest = {"allowed_targets": ["https://api.example.com"], "authorized_risks": []}  # high not authorized

        results = evaluate_all_capabilities(facts, project_scope, auth_manifest, registry)

        high_risk_result = next(r for r in results if r.capability_id == "test_high_risk")
        assert high_risk_result.state == "Awaiting authorization"
        assert "requires explicit authorization" in high_risk_result.reason

    def test_high_risk_authorized(self):
        """High risk capabilities work when authorized."""
        from asta.capability import CapabilityRegistry, Capability, CapabilitySignal, evaluate_all_capabilities

        registry = CapabilityRegistry()
        registry.register(Capability(
            capability_id="test_high_risk",
            name="Test High Risk",
            description="Test capability with high risk",
            adapter_id="test_adapter",
            test_types=["api"],
            risk_level="high",
            signals=[
                CapabilitySignal(
                    name="openapi_spec",
                    category="api_spec",
                    required=True,
                    description="OpenAPI spec"
                ),
                CapabilitySignal(
                    name="api_target_authorized",
                    category="authorization",
                    required=True,
                    description="API target authorized"
                )
            ],
            prerequisites=[]
        ))

        facts = self.create_api_project_facts()
        project_scope = {"types": ["api"], "risk_approval": "high"}
        auth_manifest = {"allowed_targets": ["https://api.example.com"], "authorized_risks": ["high"]}

        results = evaluate_all_capabilities(facts, project_scope, auth_manifest, registry)

        high_risk_result = next(r for r in results if r.capability_id == "test_high_risk")
        assert high_risk_result.state == "Applicable"
        assert "All required signals satisfied" in high_risk_result.reason

    def test_httpx_api_assert_applicable(self):
        """httpx_api_assert applicable with authorized target."""
        facts = self.create_api_project_facts()
        project_scope = {"types": ["api"], "risk_approval": "low"}
        auth_manifest = {"allowed_targets": ["https://api.example.com"], "authorized_risks": []}

        results = evaluate_all_capabilities(facts, project_scope, auth_manifest)

        httpx_result = next(r for r in results if r.capability_id == "httpx_api_assert")
        assert httpx_result.state == "Applicable"

    def test_unsupported_condition_python_version(self):
        """Unsupported condition triggers for old Python."""
        # This test would need a mock with old Python version
        # For now, verify the condition exists
        registry = CapabilityRegistry()
        cap = registry.get("pytest_unit")
        assert "Python version < 3.12" in cap.unsupported_conditions

    def test_get_applicable_capabilities(self):
        """Get applicable capability IDs."""
        facts = self.create_python_project_facts()
        project_scope = {"types": ["unit"], "risk_approval": "low"}
        auth_manifest = {"allowed_targets": [], "authorized_risks": []}

        applicable = get_applicable_capabilities(facts, project_scope, auth_manifest)

        assert "pytest_unit" in applicable
        # pytest_integration needs integration test files
        # schemathesis_api needs OpenAPI spec
        # httpx_api_assert needs authorized target

    def test_unsupported_conditions_no_manifest(self):
        """Capabilities unsupported when no Python manifest."""
        facts = []  # No facts
        project_scope = {"types": ["unit"], "risk_approval": "low"}
        auth_manifest = {"allowed_targets": [], "authorized_risks": []}

        results = evaluate_all_capabilities(facts, project_scope, auth_manifest)

        pytest_result = next(r for r in results if r.capability_id == "pytest_unit")
        assert pytest_result.state == "Unsupported"
        assert "No Python project manifest found" in pytest_result.reason


class TestCapabilitySerialization:
    """Test capability serialization."""

    def test_capability_to_dict(self):
        """Capability serializes to dict."""
        cap = Capability(
            capability_id="test_cap",
            name="Test Capability",
            description="Test",
            adapter_id="test_adapter",
            test_types=["unit"],
            risk_level="low",
            signals=[CapabilitySignal(name="signal1", category="test", required=True, description="Test signal")]
        )

        data = cap.to_dict()

        assert data["capability_id"] == "test_cap"
        assert data["name"] == "Test Capability"
        assert data["test_types"] == ["unit"]
        assert data["risk_level"] == "low"
        assert len(data["signals"]) == 1
        assert data["signals"][0]["name"] == "signal1"

    def test_signal_to_dict(self):
        """CapabilitySignal serializes to dict."""
        signal = CapabilitySignal(
            name="test_signal",
            category="test",
            required=True,
            description="A test signal"
        )

        data = signal.to_dict()

        assert data["name"] == "test_signal"
        assert data["category"] == "test"
        assert data["required"] == True
        assert data["description"] == "A test signal"

    def test_applicability_result_to_dict(self):
        """ApplicabilityResult serializes to dict."""
        result = ApplicabilityResult(
            capability_id="test_cap",
            state=ApplicabilityState.APPLICABLE,
            reason="All signals satisfied",
            prerequisites=[],
            evidence=["evidence1", "evidence2"]
        )

        data = result.to_dict()

        assert data["capability_id"] == "test_cap"
        assert data["state"] == "Applicable"
        assert data["reason"] == "All signals satisfied"
        assert data["evidence"] == ["evidence1", "evidence2"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])