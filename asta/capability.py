#!/usr/bin/env python3
"""
ASTA M1 Capability Registry

Registers capabilities (adapters) and evaluates their applicability against project signals.
States: Applicable, Not applicable, Unsupported, Blocked, Awaiting authorization.
Project signals do not authorize execution.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import json
from datetime import datetime

# ==============================================================================
# Capability State Enum
# ==============================================================================

class ApplicabilityState(str, Enum):
    """Applicability state of a capability for a given project."""
    APPLICABLE = "Applicable"
    NOT_APPLICABLE = "Not applicable"
    UNSUPPORTED = "Unsupported"
    BLOCKED = "Blocked"
    AWAITING_AUTHORIZATION = "Awaiting authorization"

@dataclass
class ApplicabilityResult:
    """Result of applicability evaluation for a capability."""
    capability_id: str
    state: str
    reason: str
    prerequisites: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    evaluated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> Dict:
        return {
            "capability_id": self.capability_id,
            "state": self.state,
            "reason": self.reason,
            "prerequisites": self.prerequisites,
            "evidence": self.evidence,
            "evaluated_at": self.evaluated_at
        }

# ==============================================================================
# Capability Definition
# ==============================================================================

@dataclass
class CapabilitySignal:
    """A signal required for a capability to be applicable."""
    name: str                    # e.g., "python_manifest", "openapi_spec", "pytest_config"
    category: str                # e.g., "manifest", "framework", "tool", "config"
    required: bool = True        # If False, optional signal
    description: str = ""

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "category": self.category,
            "required": self.required,
            "description": self.description
        }

@dataclass
class Capability:
    """A testing capability provided by an adapter."""
    capability_id: str                    # e.g., "pytest_unit", "schemathesis_api"
    name: str                             # Human-readable name
    description: str
    adapter_id: str                       # e.g., "pytest_adapter", "schemathesis_adapter"
    test_types: List[str]                 # e.g., ["unit"], ["api"]
    risk_level: str                       # low, medium, high, critical
    signals: List[Dict] = field(default_factory=list)  # Required/optional signals
    prerequisites: List[str] = field(default_factory=list)  # External prerequisites
    supported_os: List[str] = field(default_factory=lambda: ["linux", "windows", "macos"])
    supported_python: str = ">=3.12"
    version: str = "1.0.0"
    license: str = "MIT"
    tool_versions: Dict[str, str] = field(default_factory=dict)  # e.g., {"pytest": "8.2.0"}
    evidence_mapping: Dict[str, str] = field(default_factory=dict)  # How evidence maps to verdict
    limits: Dict[str, Any] = field(default_factory=dict)  # Resource limits
    unsupported_conditions: List[str] = field(default_factory=list)  # Known unsupported cases

    def to_dict(self) -> Dict:
        return {
            "capability_id": self.capability_id,
            "name": self.name,
            "description": self.description,
            "adapter_id": self.adapter_id,
            "test_types": self.test_types,
            "risk_level": self.risk_level,
            "signals": [s.to_dict() if hasattr(s, 'to_dict') else s for s in self.signals],
            "prerequisites": self.prerequisites,
            "supported_os": self.supported_os,
            "supported_python": self.supported_python,
            "version": self.version,
            "license": self.license,
            "tool_versions": self.tool_versions,
            "evidence_mapping": self.evidence_mapping,
            "limits": self.limits,
            "unsupported_conditions": self.unsupported_conditions
        }

# ==============================================================================
# Capability Registry
# ==============================================================================

class CapabilityRegistry:
    """Registry of all available capabilities with applicability evaluation."""

    def __init__(self):
        self.capabilities: Dict[str, Capability] = {}
        self._register_builtin_capabilities()

    def _register_builtin_capabilities(self):
        """Register M1 built-in capabilities."""

        # ================================================================
        # Pytest Unit Testing Capability
        # ================================================================
        self.register(Capability(
            capability_id="pytest_unit",
            name="Python Unit Testing (pytest)",
            description="Execute existing pytest unit tests in isolated worker",
            adapter_id="pytest_adapter",
            test_types=["unit"],
            risk_level="low",
            signals=[
                CapabilitySignal(
                    name="python_manifest",
                    category="manifest",
                    required=True,
                    description="Python project manifest (pyproject.toml, setup.py, requirements.txt)"
                ),
                CapabilitySignal(
                    name="pytest_config",
                    category="tool",
                    required=True,
                    description="pytest configuration (pytest.ini, pyproject.toml [tool.pytest])"
                ),
                CapabilitySignal(
                    name="test_files",
                    category="test_file",
                    required=True,
                    description="Test files detected (test_*.py, *_test.py)"
                )
            ],
            prerequisites=["pytest>=8.2.0", "Python 3.12+"],
            supported_os=["linux"],
            supported_python=">=3.12",
            version="1.0.0",
            license="MIT",
            tool_versions={"pytest": "8.2.0"},
            evidence_mapping={
                "exit_code_0": "Passed",
                "exit_code_1": "Failed",
                "exit_code_5": "Skipped",
                "exit_code_2": "Error"
            },
            limits={
                "timeout_seconds": 300,
                "memory_mb": 2048,
                "cpu_cores": 2.0,
                "process_limit": 50,
                "output_mb": 5
            },
            unsupported_conditions=[
                "No Python project manifest found",
                "No pytest configuration found",
                "No test files found",
                "Python version < 3.12"
            ]
        ))

        # ================================================================
        # Pytest Integration Testing Capability
        # ================================================================
        self.register(Capability(
            capability_id="pytest_integration",
            name="Python Integration Testing (pytest)",
            description="Execute existing pytest integration tests in isolated worker",
            adapter_id="pytest_adapter",
            test_types=["integration"],
            risk_level="medium",
            signals=[
                CapabilitySignal(
                    name="python_manifest",
                    category="manifest",
                    required=True,
                    description="Python project manifest"
                ),
                CapabilitySignal(
                    name="pytest_config",
                    category="tool",
                    required=True,
                    description="pytest configuration"
                ),
                CapabilitySignal(
                    name="integration_test_files",
                    category="test_file",
                    required=True,
                    description="Integration test files (tests/integration/, test_integration.py)"
                ),
                CapabilitySignal(
                    name="service_dependencies",
                    category="config",
                    required=False,
                    description="Service dependencies (databases, message queues) in docker-compose"
                )
            ],
            prerequisites=["pytest>=8.2.0", "Python 3.12+", "Docker (for service deps)"],
            supported_os=["linux"],
            supported_python=">=3.12",
            version="1.0.0",
            license="MIT",
            tool_versions={"pytest": "8.2.0"},
            evidence_mapping={
                "exit_code_0": "Passed",
                "exit_code_1": "Failed",
                "exit_code_5": "Skipped",
                "exit_code_2": "Error"
            },
            limits={
                "timeout_seconds": 300,
                "memory_mb": 2048,
                "cpu_cores": 2.0,
                "process_limit": 50,
                "output_mb": 5
            },
            unsupported_conditions=[
                "No integration test files found",
                "Required service dependencies not available",
                "Python version < 3.12"
            ]
        ))

        # ================================================================
        # Schemathesis API Testing Capability
        # ================================================================
        self.register(Capability(
            capability_id="schemathesis_api",
            name="API Contract Testing (Schemathesis)",
            description="Generate and execute API tests from OpenAPI specification",
            adapter_id="schemathesis_adapter",
            test_types=["api"],
            risk_level="medium",
            signals=[
                CapabilitySignal(
                    name="openapi_spec",
                    category="api_spec",
                    required=True,
                    description="OpenAPI 3.0 specification file (openapi.json/yaml, swagger.json/yaml)"
                ),
                CapabilitySignal(
                    name="api_target_authorized",
                    category="authorization",
                    required=True,
                    description="API target explicitly authorized in scope manifest"
                ),
                CapabilitySignal(
                    name="network_access",
                    category="network",
                    required=True,
                    description="Network egress to target API permitted"
                )
            ],
            prerequisites=["schemathesis>=5.6.0", "httpx>=0.27.0", "Python 3.12+"],
            supported_os=["linux"],
            supported_python=">=3.12",
            version="1.0.0",
            license="MIT",
            tool_versions={"schemathesis": "5.6.0", "httpx": "0.27.0"},
            evidence_mapping={
                "status_pass": "Passed",
                "status_fail": "Failed",
                "status_error": "Error",
                "no_test_cases": "Inconclusive"
            },
            limits={
                "timeout_seconds": 300,
                "memory_mb": 2048,
                "cpu_cores": 2.0,
                "process_limit": 50,
                "output_mb": 5,
                "api_rate_limit": 60  # requests/minute
            },
            unsupported_conditions=[
                "OpenAPI version not 3.0.x",
                "Schemathesis version incompatible"
            ]
        ))

        # ================================================================
        # HTTPX API Assertion Capability (fallback)
        # ================================================================
        self.register(Capability(
            capability_id="httpx_api_assert",
            name="API Assertion Testing (HTTPX)",
            description="Execute deterministic HTTP assertions against authorized API endpoints",
            adapter_id="httpx_adapter",
            test_types=["api"],
            risk_level="low",
            signals=[
                CapabilitySignal(
                    name="api_target_authorized",
                    category="authorization",
                    required=True,
                    description="API target explicitly authorized"
                ),
                CapabilitySignal(
                    name="assertion_definitions",
                    category="config",
                    required=True,
                    description="Assertion definitions in asta.toml or separate config"
                ),
                CapabilitySignal(
                    name="network_access",
                    category="network",
                    required=True,
                    description="Network egress to target API permitted"
                )
            ],
            prerequisites=["httpx>=0.27.0", "Python 3.12+"],
            supported_os=["linux"],
            supported_python=">=3.12",
            version="1.0.0",
            license="MIT",
            tool_versions={"httpx": "0.27.0"},
            evidence_mapping={
                "all_assertions_pass": "Passed",
                "any_assertion_fail": "Failed",
                "assertion_error": "Error"
            },
            limits={
                "timeout_seconds": 300,
                "memory_mb": 512,
                "cpu_cores": 1.0,
                "process_limit": 10,
                "output_mb": 2,
                "api_rate_limit": 60
            },
            unsupported_conditions=[
                "No authorized API target",
                "No assertion definitions"
            ]
        ))

    def register(self, capability: Capability) -> None:
        """Register a capability in the registry."""
        self.capabilities[capability.capability_id] = capability

    def get(self, capability_id: str) -> Optional[Capability]:
        """Get a capability by ID."""
        return self.capabilities.get(capability_id)

    def list_all(self) -> List[Capability]:
        """List all registered capabilities."""
        return list(self.capabilities.values())

    def list_by_test_type(self, test_type: str) -> List[Capability]:
        """List capabilities supporting a test type."""
        return [c for c in self.capabilities.values() if test_type in c.test_types]

    def list_by_adapter(self, adapter_id: str) -> List[Capability]:
        """List capabilities provided by an adapter."""
        return [c for c in self.capabilities.values() if c.adapter_id == adapter_id]


# ==============================================================================
# Applicability Evaluation
# ==============================================================================

class ApplicabilityState(str, Enum):
    APPLICABLE = "Applicable"
    NOT_APPLICABLE = "Not applicable"
    UNSUPPORTED = "Unsupported"
    BLOCKED = "Blocked"
    AWAITING_AUTHORIZATION = "Awaiting authorization"

@dataclass
class ApplicabilityResult:
    capability_id: str
    state: str
    reason: str
    prerequisites: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    evaluated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> Dict:
        return {
            "capability_id": self.capability_id,
            "state": self.state,
            "reason": self.reason,
            "prerequisites": self.prerequisites,
            "evidence": self.evidence,
            "evaluated_at": self.evaluated_at
        }


class ApplicabilityEvaluator:
    """Evaluates capability applicability against project inspection results."""

    def __init__(self, registry: CapabilityRegistry):
        self.registry = registry

    def evaluate(self,
                 capability_id: str,
                 inspection_facts: List[Dict],
                 project_scope: Dict,
                 authorization_manifest: Dict) -> 'ApplicabilityResult':
        """Evaluate a single capability's applicability."""
        capability = self.registry.get(capability_id)
        if not capability:
            return ApplicabilityResult(
                capability_id=capability_id,
                state="Unsupported",
                reason=f"Capability {capability_id} not registered"
            )

        # Convert facts to lookup dict
        facts_by_category = {}
        for fact in inspection_facts:
            cat = fact.get("category")
            if cat not in facts_by_category:
                facts_by_category[cat] = []
            facts_by_category[cat].append(fact)

        # Evaluate each required signal
        missing_required = []
        missing_optional = []
        satisfied = []
        evidence = []

        for signal in capability.signals:
            found = self._check_signal(signal, facts_by_category, project_scope, authorization_manifest)
            if found:
                satisfied.append(signal.name)
                # Collect evidence
                for fact in facts_by_category.get(signal.category, []):
                    if fact.get("name") == signal.name or signal.name in fact.get("name", ""):
                        evidence.extend(fact.get("evidence", []))
            else:
                if signal.required:
                    missing_required.append(signal.name)
                else:
                    missing_optional.append(signal.name)

        # Check unsupported conditions
        for condition in capability.unsupported_conditions:
            if self._check_unsupported_condition(condition, facts_by_category, project_scope):
                return ApplicabilityResult(
                    capability_id=capability.capability_id,
                    state="Unsupported",
                    reason=condition,
                    evidence=evidence
                )

        # Check prerequisites (external)
        missing_prereqs = self._check_prerequisites(capability.prerequisites)
        if missing_prereqs:
            return ApplicabilityResult(
                capability_id=capability.capability_id,
                state="Blocked",
                reason=f"Missing prerequisites: {', '.join(missing_prereqs)}",
                prerequisites=missing_prereqs,
                evidence=evidence
            )

        # Check risk authorization
        risk_auth_result = self._check_risk_authorization(capability, authorization_manifest)
        if risk_auth_result:
            return risk_auth_result

        # Determine final state
        if missing_required:
            return ApplicabilityResult(
                capability_id=capability.capability_id,
                state="Not applicable",
                reason=f"Missing required signals: {', '.join(missing_required)}",
                evidence=evidence
            )

        if missing_optional:
            return ApplicabilityResult(
                capability_id=capability.capability_id,
                state="Applicable",
                reason=f"Applicable with optional signals missing: {', '.join(missing_optional)}",
                evidence=evidence
            )

        # All required signals satisfied
        return ApplicabilityResult(
            capability_id=capability.capability_id,
            state="Applicable",
            reason="All required signals satisfied",
            evidence=evidence
        )

    def _check_signal(self, signal: CapabilitySignal,
                      facts_by_category: Dict,
                      project_scope: Dict,
                      authorization_manifest: Dict) -> bool:
        """Check if a signal is satisfied by inspection facts."""

        if signal.name == "python_manifest":
            manifests = facts_by_category.get("manifest", [])
            python_manifests = ["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "Pipfile", "poetry.lock"]
            return any(f.get("name") in python_manifests for f in manifests)

        elif signal.name == "pytest_config":
            # Check for pytest config files
            for cat in ["manifest", "tool"]:
                for fact in facts_by_category.get(cat, []):
                    if "pytest" in fact.get("name", "").lower():
                        return True
            return False

        elif signal.name == "test_files":
            test_files = facts_by_category.get("test_file", [])
            return any("python" in f.get("name", "").lower() for f in test_files)

        elif signal.name == "integration_test_files":
            # Check for integration test files
            for fact in facts_by_category.get("test_file", []):
                name = fact.get("name", "").lower()
                if "integration" in name:
                    return True
            return False

        elif signal.name == "openapi_spec":
            api_specs = facts_by_category.get("api_spec", [])
            return len(api_specs) > 0

        elif signal.name == "api_target_authorized":
            # Check authorization manifest
            authorized_targets = authorization_manifest.get("allowed_targets", [])
            return len(authorized_targets) > 0

        elif signal.name == "network_access":
            # Network access depends on scope and policy
            # In M1, network is deny-by-default but can be granted per-check
            return True  # Will be enforced at execution time

        elif signal.name == "pytest_config":
            for cat in ["manifest", "config", "tool"]:
                for fact in facts_by_category.get(cat, []):
                    if "pytest" in fact.get("name", "").lower():
                        return True
            return False

        elif signal.name == "service_dependencies":
            # Check for docker-compose with services
            deploy = facts_by_category.get("deployment", [])
            return any("docker" in f.get("name", "").lower() for f in deploy)

        elif signal.name == "assertion_definitions":
            # Check for assertion definitions in config
            return True  # Placeholder - would check asta.toml

        return False

    def _check_unsupported_condition(self, condition: str,
                                     facts_by_category: Dict,
                                     project_scope: Dict) -> bool:
        """Check if an unsupported condition applies."""
        condition_lower = condition.lower()

        if "python version < 3.12" in condition_lower:
            # Check Python version
            for fact in facts_by_category.get("language", []):
                if fact.get("name") == "primary" and fact.get("value") == "python":
                    # Would need version check - simplified for now
                    return False

        if "no python project manifest" in condition_lower:
            manifests = facts_by_category.get("manifest", [])
            python_manifests = ["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "Pipfile", "poetry.lock"]
            return not any(f.get("name") in python_manifests for f in manifests)

        if "no pytest configuration" in condition_lower:
            for cat in ["manifest", "config", "tool"]:
                for fact in facts_by_category.get(cat, []):
                    if "pytest" in fact.get("name", "").lower():
                        return False
            return True

        if "no test files" in condition_lower:
            test_files = facts_by_category.get("test_file", [])
            python_tests = [f for f in test_files if "python" in f.get("name", "").lower()]
            return len(python_tests) == 0

        if "no openapi specification" in condition_lower:
            api_specs = facts_by_category.get("api_spec", [])
            return len(api_specs) == 0

        if "openapi version not 3.0" in condition_lower:
            for fact in facts_by_category.get("api_spec", []):
                value = fact.get("value", "")
                if "3.0" not in value and "3.1" not in value:
                    return True
            return False

        if "api target not authorized" in condition_lower:
            return True  # Will be checked via authorization

        if "network egress denied" in condition_lower:
            return True  # Will be enforced at execution

        return False

    def _check_prerequisites(self, prerequisites: List[str]) -> List[str]:
        """Check external prerequisites."""
        missing = []
        for prereq in prerequisites:
            # Simplified check - in reality would check installed tools
            if "pytest" in prereq and "8.2" in prereq:
                # Would check pytest version
                pass
            elif "python" in prereq and "3.12" in prereq:
                # Would check Python version
                pass
            elif "docker" in prereq.lower():
                # Would check Docker availability
                pass
        return missing

    def _check_risk_authorization(self, capability: Capability,
                                  authorization_manifest: Dict) -> Optional[ApplicabilityResult]:
        """Check if risk authorization is required and granted."""
        risk_level = capability.risk_level

        if risk_level in ["high", "critical"]:
            # Check if authorized in manifest
            authorized_risks = authorization_manifest.get("authorized_risks", [])
            if risk_level not in authorized_risks:
                return ApplicabilityResult(
                    capability_id=capability.capability_id,
                    state="Awaiting authorization",
                    reason=f"Risk level '{risk_level}' requires explicit authorization",
                    prerequisites=[f"Authorization for {risk_level} risk"]
                )

        return None

    def evaluate_all_capabilities(self,
                                  inspection_facts: List[Dict],
                                  project_scope: Dict,
                                  authorization_manifest: Dict) -> List[ApplicabilityResult]:
        """Evaluate all registered capabilities against project."""
        results = []
        for capability in self.registry.list_all():
            result = self.evaluate(capability.capability_id, inspection_facts, project_scope, authorization_manifest)
            results.append(result)
        return results


# ==============================================================================
# Public API
# ==============================================================================

def evaluate_all_capabilities(inspection_facts: List[Dict],
                              project_scope: Dict,
                              authorization_manifest: Dict,
                              registry: Optional[CapabilityRegistry] = None) -> List[ApplicabilityResult]:
    """Evaluate all registered capabilities against project."""
    registry = registry or CapabilityRegistry()
    evaluator = ApplicabilityEvaluator(registry)
    return evaluator.evaluate_all_capabilities(inspection_facts, project_scope, authorization_manifest)

def get_applicable_capabilities(inspection_facts: List[Dict],
                                project_scope: Dict,
                                authorization_manifest: Dict,
                                registry: Optional[CapabilityRegistry] = None) -> List[str]:
    """Get list of applicable capability IDs."""
    registry = registry or CapabilityRegistry()
    evaluator = ApplicabilityEvaluator(registry)
    results = evaluator.evaluate_all_capabilities(inspection_facts, project_scope, authorization_manifest)
    return [r.capability_id for r in results if r.state == "Applicable"]

def get_capability_states(inspection_facts: List[Dict],
                          project_scope: Dict,
                          authorization_manifest: Dict,
                          registry: Optional[CapabilityRegistry] = None) -> Dict[str, 'ApplicabilityResult']:
    """Get full applicability state for all capabilities."""
    registry = registry or CapabilityRegistry()
    evaluator = ApplicabilityEvaluator(registry)
    results = evaluator.evaluate_all_capabilities(inspection_facts, project_scope, authorization_manifest)
    return {r.capability_id: r for r in results}


# ==============================================================================
# CLI Integration
# ==============================================================================

if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) > 1:
        # Load inspection facts from file
        facts_file = sys.argv[1]
        with open(facts_file) as f:
            facts = json.load(f)

        project_scope = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
        auth_manifest = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}

        results = evaluate_all_capabilities(
            inspection_facts=facts.get("facts", []),
            project_scope=project_scope,
            authorization_manifest=auth_manifest
        )

        for r in results:
            print(f"{r['capability_id']}: {r['state']} - {r['reason']}")
    else:
        print("Usage: python -m asta.capability <inspection_facts.json> [project_scope.json] [auth_manifest.json]")