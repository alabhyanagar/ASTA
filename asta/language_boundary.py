#!/usr/bin/env python3
"""
ASTA M1 Language Boundary Decision Engine

Enforces language-boundary decisions per check:
- White-box unit checks require target module language and compatible runtime/build ecosystem
- Black-box API checks may use another supported test language against isolated target
- Component/integration must declare white-box or black-box before language binding
- No silent substitution
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import json
from datetime import datetime, timezone

# ==============================================================================
# Language Boundary Enums
# ==============================================================================

class LanguageBoundary(str, Enum):
    """Language boundary classification for a check."""
    WHITE_BOX = "white_box"      # Test runs in same language as target
    BLACK_BOX = "black_box"      # Test runs in different language, targets isolated endpoint
    HYBRID = "hybrid"            # Mix of both (not allowed in M1 without explicit declaration)

class TestLanguage(str, Enum):
    """Supported test execution languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    JAVA = "java"
    RUST = "rust"
    CSHARP = "csharp"
    RUBY = "ruby"
    PHP = "php"

class TargetType(str, Enum):
    """Type of target being tested."""
    SOURCE_CODE = "source_code"        # White-box: test has access to source
    COMPILED_ARTIFACT = "compiled_artifact"  # White-box: test has access to compiled output
    RUNNING_SERVICE = "running_service"  # Black-box: test against running endpoint
    API_ENDPOINT = "api_endpoint"      # Black-box: test against API
    DATABASE = "database"              # Black-box: test against database
    MESSAGE_QUEUE = "message_queue"    # Black-box: test against queue

# ==============================================================================
# Language Binding Configuration
# ==============================================================================

@dataclass(frozen=True)
class LanguageBinding:
    """Language binding configuration for a check."""
    check_key: str
    capability_id: str
    test_language: TestLanguage
    target_language: TestLanguage
    target_type: TargetType
    boundary: LanguageBoundary
    requires_same_runtime: bool = True  # For white-box: must have compatible runtime
    runtime_ecosystem: Optional[str] = None  # e.g., "pytest", "jest", "go test"
    binding_declared: bool = False  # Must be explicitly declared for component/integration
    declaration_source: str = ""  # "capability", "plan", "user"

    def to_dict(self) -> Dict:
        return {
            "check_key": self.check_key,
            "capability_id": self.capability_id,
            "test_language": self.test_language.value if hasattr(self.test_language, "value") else str(self.test_language),
            "target_language": self.target_language.value if hasattr(self.target_language, "value") else str(self.target_language),
            "target_type": self.target_type.value if hasattr(self.target_type, "value") else str(self.target_type),
            "boundary": self.boundary.value if hasattr(self.boundary, "value") else str(self.boundary),
            "requires_same_runtime": self.requires_same_runtime,
            "runtime_ecosystem": self.runtime_ecosystem,
            "binding_declared": self.binding_declared,
            "declaration_source": self.declaration_source
        }

@dataclass
class LanguageCompatibility:
    """Language compatibility matrix."""
    test_language: TestLanguage
    compatible_target_languages: List[TestLanguage] = field(default_factory=list)
    compatible_runtimes: List[str] = field(default_factory=list)
    white_box_supported: bool = True
    black_box_supported: bool = True

# ==============================================================================
# Language Compatibility Matrix
# ==============================================================================

# M1 Language Compatibility Matrix
# Defines which test languages can test which target languages
# and what runtime ecosystems are required
LANGUAGE_COMPATIBILITY_MATRIX: Dict[TestLanguage, LanguageCompatibility] = {
    TestLanguage.PYTHON: LanguageCompatibility(
        test_language=TestLanguage.PYTHON,
        compatible_target_languages=[
            TestLanguage.PYTHON
        ],
        compatible_runtimes=["pytest", "unittest", "tox"],
        white_box_supported=True,
        black_box_supported=True  # Can test APIs via HTTPX/Schemathesis
    ),
    TestLanguage.JAVASCRIPT: LanguageCompatibility(
        test_language=TestLanguage.JAVASCRIPT,
        compatible_target_languages=[
            TestLanguage.JAVASCRIPT,
            TestLanguage.TYPESCRIPT
        ],
        compatible_runtimes=["jest", "mocha", "vitest", "playwright"],
        white_box_supported=True,
        black_box_supported=True
    ),
    TestLanguage.TYPESCRIPT: LanguageCompatibility(
        test_language=TestLanguage.TYPESCRIPT,
        compatible_target_languages=[
            TestLanguage.TYPESCRIPT,
            TestLanguage.JAVASCRIPT
        ],
        compatible_runtimes=["jest", "vitest", "playwright"],
        white_box_supported=True,
        black_box_supported=True
    ),
    TestLanguage.GO: LanguageCompatibility(
        test_language=TestLanguage.GO,
        compatible_target_languages=[
            TestLanguage.GO
        ],
        compatible_runtimes=["go test"],
        white_box_supported=True,
        black_box_supported=True
    ),
    TestLanguage.JAVA: LanguageCompatibility(
        test_language=TestLanguage.JAVA,
        compatible_target_languages=[
            TestLanguage.JAVA,
            TestLanguage.KOTLIN if hasattr(TestLanguage, 'KOTLIN') else TestLanguage.JAVA
        ],
        compatible_runtimes=["junit", "testng", "maven", "gradle"],
        white_box_supported=True,
        black_box_supported=True
    ),
    TestLanguage.RUST: LanguageCompatibility(
        test_language=TestLanguage.RUST,
        compatible_target_languages=[
            TestLanguage.RUST
        ],
        compatible_runtimes=["cargo test"],
        white_box_supported=True,
        black_box_supported=True
    ),
    TestLanguage.CSHARP: LanguageCompatibility(
        test_language=TestLanguage.CSHARP,
        compatible_target_languages=[
            TestLanguage.CSHARP,
            TestLanguage.FSHARP if hasattr(TestLanguage, 'FSHARP') else TestLanguage.CSHARP
        ],
        compatible_runtimes=["dotnet test", "nunit", "xunit"],
        white_box_supported=True,
        black_box_supported=True
    ),
}

# M1 Supported Test Languages
M1_SUPPORTED_TEST_LANGUAGES = [
    TestLanguage.PYTHON
]

# M1 Supported Target Languages
M1_SUPPORTED_TARGET_LANGUAGES = [
    TestLanguage.PYTHON
]

# ==============================================================================
# Language Binding Engine
# ==============================================================================

class LanguageBoundaryEngine:
    """Engine for determining and enforcing language boundaries per check."""

    def __init__(self):
        self.bindings: Dict[str, LanguageBinding] = {}
        self.declarations: Dict[str, Dict] = {}  # check_key -> declaration

    def determine_binding(self,
                          capability_id: str,
                          project_profile: Dict,
                          capability_registry: 'CapabilityRegistry',
                          project_scope: Dict) -> LanguageBinding:
        """
        Determine the language binding for a capability.

        Rules:
        1. Check capability definition for explicit boundary
        2. If component/integration: must have explicit declaration
        3. White-box: test language must match target language
        4. Black-box: test language can differ, but must be supported
        5. No silent substitution - all decisions explicit
        """
        from asta.capability import CapabilityRegistry

        capability = capability_registry.get(capability_id)
        if not capability:
            raise ValueError(f"Capability {capability_id} not found")

        # Get project's primary language
        target_language = self._get_target_language(project_profile)

        # Determine boundary from capability
        boundary = self._determine_boundary(capability)

        # For M1, only Python is supported
        test_language = TestLanguage.PYTHON
        target_language = TestLanguage.PYTHON  # M1 only supports Python targets

        # Determine target type
        target_type = self._determine_target_type(capability, boundary)

        # Check if declaration required
        binding_declared = self._requires_declaration(capability, boundary)
        declaration_source = self._get_declaration_source(capability, boundary)

        binding = LanguageBinding(
            check_key=f"{capability_id}_binding",
            capability_id=capability_id,
            test_language=test_language,
            target_language=target_language,
            target_type=target_type,
            boundary=boundary,
            requires_same_runtime=(boundary == LanguageBoundary.WHITE_BOX),
            runtime_ecosystem=self._get_runtime_ecosystem(capability),
            binding_declared=binding_declared,
            declaration_source=declaration_source
        )

        self.bindings[capability_id] = binding
        return binding

    def _get_target_language(self, project_profile: Dict) -> TestLanguage:
        """Get target language from project profile."""
        detected = project_profile.get("language", "unknown")
        try:
            return TestLanguage(detected)
        except ValueError:
            return TestLanguage.PYTHON  # Default for M1

    def _determine_boundary(self, capability: Any) -> LanguageBoundary:
        """Determine language boundary from capability."""
        # Helper to get attribute or dict item
        def _get(obj, key, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        # Capability can define boundary in its metadata
        boundary_val = _get(capability, "boundary")
        if boundary_val is not None:
            return LanguageBoundary(boundary_val)

        adapter_id = _get(capability, "adapter_id")
        if adapter_id in ["pytest_adapter"]:
            return LanguageBoundary.WHITE_BOX
        elif adapter_id in ["schemathesis_adapter", "httpx_adapter"]:
            return LanguageBoundary.BLACK_BOX

        # Default
        return LanguageBoundary.WHITE_BOX

    def _determine_target_type(self, capability: Any, boundary: LanguageBoundary) -> str:
        """Determine target type from capability and boundary."""
        def _get(obj, key, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        adapter_id = _get(capability, "adapter_id")
        if boundary == LanguageBoundary.WHITE_BOX:
            if adapter_id == "pytest_adapter":
                return "source_code"
            return "source_code"
        else:
            if adapter_id in ["schemathesis_adapter", "httpx_adapter"]:
                return "api_endpoint"
            return "running_service"

    def _requires_declaration(self, capability: Any, boundary: LanguageBoundary) -> bool:
        """Check if explicit declaration is required."""
        def _get(obj, key, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        test_types = _get(capability, "test_types") or []
        if any(t in ["component", "integration"] for t in test_types):
            return True
        if boundary == LanguageBoundary.BLACK_BOX:
            return False
        return False

    def _get_declaration_source(self, capability: Any, boundary: LanguageBoundary) -> str:
        """Get the source of boundary declaration."""
        if self._requires_declaration(capability, boundary):
            return "plan"
        return "capability"

    def _get_runtime_ecosystem(self, capability: Any) -> Optional[str]:
        """Get required runtime ecosystem."""
        def _get(obj, key, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        adapter_id = _get(capability, "adapter_id")
        if adapter_id == "pytest_adapter":
            return "pytest"
        elif adapter_id == "schemathesis_adapter":
            return "schemathesis"
        elif adapter_id == "httpx_adapter":
            return "httpx"
        return None

    def validate_binding(self, binding: LanguageBinding, project_profile: Dict) -> Tuple[bool, str]:
        """Validate a language binding against project profile."""

        # Check test language is supported
        if binding.test_language not in M1_SUPPORTED_TEST_LANGUAGES:
            return False, f"Test language {binding.test_language.value} not supported in M1"

        # Check target language is supported
        if binding.target_language not in M1_SUPPORTED_TARGET_LANGUAGES:
            if binding.boundary == LanguageBoundary.WHITE_BOX and binding.test_language != binding.target_language:
                return False, f"White-box requires test language ({binding.test_language.value}) to match target language ({binding.target_language.value})"
            return False, f"Target language {binding.target_language.value} not supported in M1"

        # White-box: test language must match target language
        if binding.boundary == LanguageBoundary.WHITE_BOX:
            if binding.test_language != binding.target_language:
                return False, f"White-box requires test language ({binding.test_language.value}) to match target language ({binding.target_language.value})"

            # Check runtime ecosystem compatibility
            if binding.runtime_ecosystem:
                compat = LANGUAGE_COMPATIBILITY_MATRIX.get(binding.test_language)
                if compat and binding.runtime_ecosystem not in compat.compatible_runtimes:
                    return False, f"Runtime {binding.runtime_ecosystem} not compatible with {binding.test_language.value}"

        # Black-box: test language can differ but both must be supported
        if binding.boundary == LanguageBoundary.BLACK_BOX:
            if binding.test_language not in M1_SUPPORTED_TEST_LANGUAGES:
                return False, f"Test language {binding.test_language.value} not supported"
            if binding.target_language not in M1_SUPPORTED_TARGET_LANGUAGES:
                return False, f"Target language {binding.target_language.value} not supported"

        # Component/integration must have explicit declaration
        if binding.binding_declared and not binding.declaration_source:
            return False, "Component/integration requires explicit boundary declaration"

        return True, "Valid"

    def get_all_bindings(self) -> Dict[str, LanguageBinding]:
        return self.bindings.copy()


# ==============================================================================
# Language Boundary Declaration
# ==============================================================================

@dataclass
class BoundaryDeclaration:
    """Explicit boundary declaration for a check."""
    check_key: str
    capability_id: str
    boundary: LanguageBoundary
    test_language: TestLanguage
    target_language: TestLanguage
    target_type: TargetType
    declared_by: str  # "user", "plan", "capability"
    declared_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    runtime_ecosystem: Optional[str] = None
    notes: str = ""

    def to_dict(self) -> Dict:
        return {
            "check_key": self.check_key,
            "capability_id": self.capability_id,
            "boundary": self.boundary.value,
            "test_language": self.test_language.value,
            "target_language": self.target_language.value,
            "target_type": self.target_type.value,
            "declared_by": self.declared_by,
            "declared_at": self.declared_at,
            "runtime_ecosystem": self.runtime_ecosystem,
            "notes": self.notes
        }

class BoundaryDeclarationManager:
    """Manages explicit boundary declarations."""

    def __init__(self):
        self.declarations: Dict[str, BoundaryDeclaration] = {}

    def declare(self, declaration: BoundaryDeclaration) -> None:
        """Record a boundary declaration."""
        self.declarations[declaration.check_key] = declaration

    def get(self, check_key: str) -> Optional[BoundaryDeclaration]:
        return self.declarations.get(check_key)

    def has_declaration(self, check_key: str) -> bool:
        return check_key in self.declarations

    def validate_declaration(self, declaration: BoundaryDeclaration, project_profile: Dict) -> Tuple[bool, str]:
        """Validate a boundary declaration."""
        # Check test language is supported
        if declaration.test_language not in M1_SUPPORTED_TEST_LANGUAGES:
            return False, f"Test language {declaration.test_language.value} not supported"

        # Check target language is supported
        if declaration.target_language not in M1_SUPPORTED_TARGET_LANGUAGES:
            if declaration.boundary == LanguageBoundary.WHITE_BOX and declaration.test_language != declaration.target_language:
                return False, "White-box requires matching test and target languages"
            return False, f"Target language {declaration.target_language.value} not supported"

        # White-box must match languages
        if declaration.boundary == LanguageBoundary.WHITE_BOX:
            if declaration.test_language != declaration.target_language:
                return False, "White-box requires matching test and target languages"

        # Check runtime ecosystem
        if declaration.runtime_ecosystem:
            compat = LANGUAGE_COMPATIBILITY_MATRIX.get(declaration.test_language)
            if compat and declaration.runtime_ecosystem not in compat.compatible_runtimes:
                return False, f"Runtime {declaration.runtime_ecosystem} not compatible with {declaration.test_language.value}"

        return True, "Valid"


# ==============================================================================
# Language Boundary Plan Integration
# ==============================================================================

def integrate_language_boundaries(plan: Any,
                                   engine: LanguageBoundaryEngine,
                                   project_profile: Dict,
                                   capability_registry: 'CapabilityRegistry',
                                   project_scope: 'ProjectScope') -> Any:
    """Add language boundary bindings to a plan."""

    from asta.capability import CapabilityRegistry

    checks = plan.checks if hasattr(plan, "checks") else plan["checks"]

    for check in checks:
        cap_id = check.capability_id if hasattr(check, "capability_id") else check.get("capability_id")
        if cap_id:
            binding = engine.determine_binding(
                capability_id=cap_id,
                project_profile=project_profile,
                capability_registry=capability_registry,
                project_scope=project_scope.to_dict() if hasattr(project_scope, "to_dict") else project_scope
            )

            # Add binding info to check
            if hasattr(check, "limits"):
                check.limits["language_binding"] = binding.to_dict()
            elif isinstance(check, dict) and "limits" in check:
                check["limits"]["language_binding"] = binding.to_dict()

            # Validate binding
            valid, reason = engine.validate_binding(binding, {})
            if not valid:
                if hasattr(check, "state"):
                    check.state = "blocked"
                    check.reason = f"Language binding invalid: {reason}"
                elif isinstance(check, dict):
                    check["state"] = "blocked"
                    check["reason"] = f"Language binding invalid: {reason}"

    return plan


# ==============================================================================
# CLI Integration
# ==============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        from asta.capability import CapabilityRegistry
        registry = CapabilityRegistry()
        engine = LanguageBoundaryEngine()

        # Test bindings
        for cap_id in ["pytest_unit", "pytest_integration", "schemathesis_api", "httpx_api_assert"]:
            binding = engine.determine_binding(
                capability_id=cap_id,
                project_profile={"language": "python"},
                capability_registry=registry,
                project_scope={"types": ["unit", "integration", "api"]}
            )
            valid, reason = engine.validate_binding(binding, {})
            print(f"{cap_id}: {binding.boundary.value} - {binding.target_type.value} - {valid}: {reason}")

    print("Language Boundary Engine ready")