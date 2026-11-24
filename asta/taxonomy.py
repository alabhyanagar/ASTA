#!/usr/bin/env python3
"""
ASTA M1 Versioned Normalized Taxonomy Model

Preserves separate dimensions: test level/strategy, domain, protocol/platform, technique, validation intent.
One check can carry multiple tags. Stable IDs/alias policy versioned before persisted runs.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import json
from datetime import datetime
import hashlib

# ==============================================================================
# Dimension Enums (Canonical Values)
# ==============================================================================

class TestLevel(str, Enum):
    """Test execution level/strategy — the 'what' of testing."""
    UNIT = "unit"
    INTEGRATION = "integration"
    COMPONENT = "component"
    SYSTEM = "system"
    API = "api"
    REGRESSION = "regression"
    SMOKE = "smoke"
    SANITY = "sanity"
    EXPLORATORY = "exploratory"
    ACCEPTANCE = "acceptance"
    PERFORMANCE = "performance"
    LOAD = "load"
    STRESS = "stress"
    ENDURANCE = "endurance"
    SPIKE = "spike"
    VOLUME = "volume"
    SECURITY = "security"
    COMPLIANCE = "compliance"

class Domain(str, Enum):
    """Software domain/category — the 'where' of testing."""
    BACKEND = "backend"
    FRONTEND = "frontend"
    FULL_STACK = "full-stack"
    MICROSERVICE = "microservice"
    MONOLITH = "monolith"
    LIBRARY = "library"
    CLI = "cli"
    MOBILE = "mobile"
    DESKTOP = "desktop"
    EMBEDDED = "embedded"
    DATABASE = "database"
    INFRASTRUCTURE = "infrastructure"

class Protocol(str, Enum):
    """Communication protocol — the 'how' of communication."""
    HTTP = "http"
    HTTPS = "https"
    GRPC = "grpc"
    WEBSOCKET = "websocket"
    GRAPHQL = "graphql"
    REST = "rest"
    SOAP = "soap"
    MQTT = "mqtt"
    AMQP = "amqp"
    KAFKA = "kafka"
    RABBITMQ = "rabbitmq"
    REDIS = "redis"
    TCP = "tcp"
    UDP = "udp"
    UNIX_SOCKET = "unix_socket"

class Technique(str, Enum):
    """Testing technique/approach — the 'method' of testing."""
    UNIT_TEST = "unit_test"
    INTEGRATION_TEST = "integration_test"
    COMPONENT_TEST = "component_test"
    SYSTEM_TEST = "system_test"
    E2E_TEST = "e2e_test"
    API_TEST = "api_test"
    CONTRACT_TEST = "contract_test"
    SCHEMA_TEST = "schema_test"
    PROPERTY_TEST = "property_test"
    FUZZ_TEST = "fuzz_test"
    MUTATION_TEST = "mutation_test"
    CHAOS_TEST = "chaos_test"
    SMOKE_TEST = "smoke_test"
    REGRESSION_TEST = "regression_test"
    PERFORMANCE_TEST = "performance_test"
    LOAD_TEST = "load_test"
    STRESS_TEST = "stress_test"
    SECURITY_TEST = "security_test"
    PENETRATION_TEST = "penetration_test"
    STATIC_ANALYSIS = "static_analysis"
    DYNAMIC_ANALYSIS = "dynamic_analysis"
    CODE_REVIEW = "code_review"
    MANUAL_TEST = "manual_test"
    EXPLORATORY_TEST = "exploratory_test"
    ACCESSIBILITY_TEST = "accessibility_test"
    USABILITY_TEST = "usability_test"
    VISUAL_TEST = "visual_test"
    CROSS_BROWSER_TEST = "cross_browser_test"
    MOBILE_TEST = "mobile_test"

class ValidationIntent(str, Enum):
    """Validation intent — the 'why' of testing."""
    FUNCTIONAL_CORRECTNESS = "functional_correctness"
    PERFORMANCE = "performance"
    SECURITY = "security"
    RELIABILITY = "reliability"
    AVAILABILITY = "availability"
    SCALABILITY = "scalability"
    COMPATIBILITY = "compatibility"
    USABILITY = "usability"
    ACCESSIBILITY = "accessibility"
    COMPLIANCE = "compliance"
    DATA_INTEGRITY = "data_integrity"
    ERROR_HANDLING = "error_handling"
    BOUNDARY_CONDITIONS = "boundary_conditions"
    EDGE_CASES = "edge_cases"
    REGRESSION_PREVENTION = "regression_prevention"
    CONTRACT_COMPLIANCE = "contract_compliance"

# ==============================================================================
# Taxonomy Versioning
# ==============================================================================

class TaxonomyVersion:
    """Taxonomy version with release metadata."""

    def __init__(self, version: str, released_at: str, description: str = ""):
        self.version = version
        self.released_at = released_at
        self.description = description

    def __str__(self):
        return f"Taxonomy v{self.version} ({self.released_at})"

# Current M1 taxonomy version
M1_TAXONOMY_VERSION = TaxonomyVersion(
    version="1.0.0",
    released_at="2026-11-23T00:00:00Z",
    description="Initial M1 taxonomy with 5 dimensions"
)

# ==============================================================================
# Canonical Check ID
# ==============================================================================

@dataclass(frozen=True)
class CanonicalCheckID:
    """
    Immutable canonical ID for a check.
    Combines dimension values into a stable, hashable identifier.
    One check can carry multiple tags across dimensions.
    """
    test_level: TestLevel
    domain: Optional[Domain] = None
    protocol: Optional[Protocol] = None
    technique: Optional[Technique] = None
    validation_intent: Optional[ValidationIntent] = None
    taxonomy_version: str = "1.0.0"

    def __post_init__(self):
        if not self.taxonomy_version:
            object.__setattr__(self, 'taxonomy_version', "1.0.0")

    def to_tuple(self) -> Tuple:
        return (
            self.test_level,
            self.domain,
            self.protocol,
            self.technique,
            self.validation_intent,
            self.taxonomy_version
        )

    def __str__(self) -> str:
        parts = [f"test_level={self.test_level.value}"]
        if self.domain:
            parts.append(f"domain={self.domain.value}")
        if self.protocol:
            parts.append(f"protocol={self.protocol.value}")
        if self.technique:
            parts.append(f"technique={self.technique.value}")
        if self.validation_intent:
            parts.append(f"validation_intent={self.validation_intent.value}")
        return "Check(" + ", ".join(parts) + ")"

    def to_dict(self) -> Dict:
        return {
            "test_level": self.test_level.value,
            "domain": self.domain.value if self.domain else None,
            "protocol": self.protocol.value if self.protocol else None,
            "technique": self.technique.value if self.technique else None,
            "validation_intent": self.validation_intent.value if self.validation_intent else None,
            "taxonomy_version": self.taxonomy_version
        }

    def get_tags(self) -> List[str]:
        tags = [self.test_level.value]
        if self.domain:
            tags.append(self.domain.value)
        if self.protocol:
            tags.append(self.protocol.value)
        if self.technique:
            tags.append(self.technique.value)
        if self.validation_intent:
            tags.append(self.validation_intent.value)
        return tags

    def matches_scope(self, scope_types: List[str]) -> bool:
        return self.test_level.value in scope_types

    @classmethod
    def from_dict(cls, data: Dict) -> 'CanonicalCheckID':
        return cls(
            test_level=TestLevel(data["test_level"]),
            domain=Domain(data["domain"]) if data.get("domain") else None,
            protocol=Protocol(data["protocol"]) if data.get("protocol") else None,
            technique=Technique(data["technique"]) if data.get("technique") else None,
            validation_intent=ValidationIntent(data["validation_intent"]) if data.get("validation_intent") else None,
            taxonomy_version=data.get("taxonomy_version", "1.0.0")
        )

# ==============================================================================
# Alias Registry (Versioned)
# ==============================================================================

@dataclass
class AliasRegistry:
    """Versioned alias mapping — user-friendly aliases → canonical IDs."""
    version: str
    aliases: Dict[str, 'CanonicalCheckID'] = field(default_factory=dict)
    reverse_aliases: Dict[str, List[str]] = field(default_factory=dict)

    def __post_init__(self):
        self._build_reverse_index()

    def _build_reverse_index(self):
        self.reverse_aliases = {}
        for alias, canonical in self.aliases.items():
            key = str(canonical)
            if key not in self.reverse_aliases:
                self.reverse_aliases[key] = []
            self.reverse_aliases[key].append(alias)

    @classmethod
    def create_v1(cls) -> 'AliasRegistry':
        registry = cls(version="1.0.0")

        # Test level aliases
        test_level_aliases = {
            "unit": [TestLevel.UNIT],
            "pyunit": [TestLevel.UNIT],
            "unit_test": [TestLevel.UNIT],
            "integration": [TestLevel.INTEGRATION],
            "integration_test": [TestLevel.INTEGRATION],
            "component": [TestLevel.COMPONENT],
            "component_test": [TestLevel.COMPONENT],
            "system": [TestLevel.SYSTEM],
            "system_test": [TestLevel.SYSTEM],
            "api": [TestLevel.API],
            "api_test": [TestLevel.API],
            "regression": [TestLevel.REGRESSION],
            "regression_test": [TestLevel.REGRESSION],
            "smoke": [TestLevel.SMOKE],
            "smoke_test": [TestLevel.SMOKE],
            "sanity": [TestLevel.SANITY],
            "sanity_test": [TestLevel.SANITY],
            "exploratory": [TestLevel.EXPLORATORY],
            "acceptance": [TestLevel.ACCEPTANCE],
            "acceptance_test": [TestLevel.ACCEPTANCE],
            "performance": [TestLevel.PERFORMANCE],
            "perf": [TestLevel.PERFORMANCE],
            "load": [TestLevel.LOAD],
            "load_test": [TestLevel.LOAD],
            "stress": [TestLevel.STRESS],
            "stress_test": [TestLevel.STRESS],
            "endurance": [TestLevel.ENDURANCE],
            "endurance_test": [TestLevel.ENDURANCE],
            "spike": [TestLevel.SPIKE],
            "spike_test": [TestLevel.SPIKE],
            "volume": [TestLevel.VOLUME],
            "volume_test": [TestLevel.VOLUME],
            "security": [TestLevel.SECURITY],
            "security_test": [TestLevel.SECURITY],
            "compliance": [TestLevel.COMPLIANCE],
        }

        # Domain aliases
        domain_aliases = {
            "backend": [TestLevel.API, Domain.BACKEND],
            "frontend": [TestLevel.SYSTEM, Domain.FRONTEND],
            "fullstack": [TestLevel.SYSTEM, Domain.FULL_STACK],
            "full_stack": [TestLevel.SYSTEM, Domain.FULL_STACK],
            "microservice": [TestLevel.INTEGRATION, Domain.MICROSERVICE],
            "monolith": [TestLevel.SYSTEM, Domain.MONOLITH],
            "library": [TestLevel.UNIT, Domain.LIBRARY],
            "cli": [TestLevel.SYSTEM, Domain.CLI],
            "mobile": [TestLevel.SYSTEM, Domain.MOBILE],
            "database": [TestLevel.INTEGRATION, Domain.DATABASE],
        }

        # Technique aliases
        technique_aliases = {
            "unit_test": [TestLevel.UNIT, Technique.UNIT_TEST],
            "integration_test": [TestLevel.INTEGRATION, Technique.INTEGRATION_TEST],
            "component_test": [TestLevel.COMPONENT, Technique.COMPONENT_TEST],
            "system_test": [TestLevel.SYSTEM, Technique.SYSTEM_TEST],
            "e2e_test": [TestLevel.SYSTEM, Technique.E2E_TEST],
            "e2e": [TestLevel.SYSTEM, Technique.E2E_TEST],
            "api_test": [TestLevel.API, Technique.API_TEST],
            "contract_test": [TestLevel.API, Technique.CONTRACT_TEST],
            "schema_test": [TestLevel.API, Technique.SCHEMA_TEST],
            "property_test": [TestLevel.UNIT, Technique.PROPERTY_TEST],
            "fuzz_test": [TestLevel.SECURITY, Technique.FUZZ_TEST],
            "mutation_test": [TestLevel.UNIT, Technique.MUTATION_TEST],
            "chaos_test": [TestLevel.SYSTEM, Technique.CHAOS_TEST],
            "smoke_test": [TestLevel.SMOKE, Technique.SMOKE_TEST],
            "regression_test": [TestLevel.REGRESSION, Technique.REGRESSION_TEST],
            "performance_test": [TestLevel.PERFORMANCE, Technique.PERFORMANCE_TEST],
            "load_test": [TestLevel.LOAD, Technique.LOAD_TEST],
            "stress_test": [TestLevel.STRESS, Technique.STRESS_TEST],
            "security_test": [TestLevel.SECURITY, Technique.SECURITY_TEST],
            "penetration_test": [TestLevel.SECURITY, Technique.PENETRATION_TEST],
            "static_analysis": [TestLevel.UNIT, Technique.STATIC_ANALYSIS],
            "dynamic_analysis": [TestLevel.INTEGRATION, Technique.DYNAMIC_ANALYSIS],
        }

        # Validation intent aliases
        intent_aliases = {
            "functional": ValidationIntent.FUNCTIONAL_CORRECTNESS,
            "correctness": ValidationIntent.FUNCTIONAL_CORRECTNESS,
            "performance": ValidationIntent.PERFORMANCE,
            "security": ValidationIntent.SECURITY,
            "reliability": ValidationIntent.RELIABILITY,
            "availability": ValidationIntent.AVAILABILITY,
            "scalability": ValidationIntent.SCALABILITY,
            "compatibility": ValidationIntent.COMPATIBILITY,
            "usability": ValidationIntent.USABILITY,
            "accessibility": ValidationIntent.ACCESSIBILITY,
            "compliance": ValidationIntent.COMPLIANCE,
            "data_integrity": ValidationIntent.DATA_INTEGRITY,
            "error_handling": ValidationIntent.ERROR_HANDLING,
            "boundary": ValidationIntent.BOUNDARY_CONDITIONS,
            "edge_cases": ValidationIntent.EDGE_CASES,
            "regression": ValidationIntent.REGRESSION_PREVENTION,
            "contract": ValidationIntent.CONTRACT_COMPLIANCE,
        }

        registry = cls(version="1.0.0")

        # Register all aliases in order of specificity (test_level_aliases first so specific aliases overwrite)
        for alias, dims in test_level_aliases.items():
            registry._add_alias(alias, CanonicalCheckID(test_level=dims[0]))

        for alias, dims in domain_aliases.items():
            registry._add_alias(alias, CanonicalCheckID(test_level=dims[0], domain=dims[1]))

        for alias, dims in technique_aliases.items():
            registry._add_alias(alias, CanonicalCheckID(test_level=dims[0], technique=dims[1]))

        for alias, intent in intent_aliases.items():
            level = TestLevel.SECURITY if alias == "security" else (TestLevel.REGRESSION if alias == "regression" else (TestLevel.PERFORMANCE if alias == "performance" else TestLevel.UNIT))
            registry._add_alias(alias, CanonicalCheckID(test_level=level, validation_intent=intent))

        return registry

    def _add_alias(self, alias: str, canonical: 'CanonicalCheckID'):
        self.aliases[alias.lower()] = canonical
        key = str(canonical)
        if key not in self.reverse_aliases:
            self.reverse_aliases[key] = []
        self.reverse_aliases[key].append(alias)

    def resolve(self, alias: str) -> Optional['CanonicalCheckID']:
        return self.aliases.get(alias.lower())

    def resolve_many(self, *alias_lists: Union[List[str], str]) -> Tuple[List['CanonicalCheckID'], List[str]]:
        canonical = []
        seen = set()
        unrecognized = []
        
        flat_aliases = []
        for item in alias_lists:
            if isinstance(item, list):
                flat_aliases.extend(item)
            elif isinstance(item, str):
                flat_aliases.append(item)

        for alias in flat_aliases:
            resolved = self.resolve(alias)
            if resolved:
                res_str = str(resolved)
                if res_str not in seen:
                    seen.add(res_str)
                    canonical.append(resolved)
            else:
                unrecognized.append(alias)
        return canonical, unrecognized

    def get_aliases_for(self, canonical: 'CanonicalCheckID') -> List[str]:
        return self.reverse_aliases.get(str(canonical), [])

    def __contains__(self, alias: str) -> bool:
        return alias.lower() in self.aliases


# ==============================================================================
# Taxonomy Registry
# ==============================================================================

class TaxonomyRegistry:
    """Complete taxonomy registry with versioned dimensions, aliases, and canonical IDs."""

    def __init__(self, version: str = "1.0.0"):
        self.version = version
        self.alias_registry = AliasRegistry.create_v1()
        self._canonical_cache: Dict[str, 'CanonicalCheckID'] = {}

    def parse_scope_input(self,
                          cli_types: Optional[List[str]] = None,
                          toml_types: Optional[List[str]] = None,
                          nl_request: Optional[str] = None) -> Tuple[List['CanonicalCheckID'], Dict]:
        """
        Parse scope from three input channels into canonical CheckIDs.
        Returns (canonical_ids, unrecognized_info).
        """
        all_aliases = []
        sources = {}

        if cli_types:
            all_aliases.extend(cli_types)
            sources["cli"] = cli_types

        if toml_types:
            all_aliases.extend(toml_types)
            sources["toml"] = toml_types

        if nl_request:
            # Simple NL keyword extraction
            nl_lower = nl_request.lower()
            keyword_map = {
                "unit": "unit", "pyunit": "unit", "unit test": "unit",
                "integration": "integration", "integration test": "integration",
                "component": "component", "component test": "component",
                "system": "system", "system test": "system",
                "api": "api", "api test": "api", "rest": "api", "graphql": "api", "grpc": "api",
                "regression": "regression", "regression test": "regression",
                "smoke": "smoke", "smoke test": "smoke",
                "sanity": "sanity", "sanity test": "sanity",
                "exploratory": "exploratory", "exploratory test": "exploratory",
                "acceptance": "acceptance", "acceptance test": "acceptance",
                "performance": "performance", "perf": "performance",
                "load": "load", "load test": "load",
                "stress": "stress", "stress test": "stress",
                "endurance": "endurance", "endurance test": "endurance",
                "spike": "spike", "spike test": "spike",
                "security": "security", "security test": "security",
                "compliance": "compliance",
            }

            for keyword, alias in keyword_map.items():
                if keyword in nl_lower:
                    all_aliases.append(alias)

            if all_aliases:
                sources["nl"] = nl_request

        # Resolve all aliases
        canonical, unrecognized = self.alias_registry.resolve_many(all_aliases)

        # Deduplicate
        seen = set()
        unique_canonical = []
        for c in canonical:
            key = str(c)
            if key not in seen:
                seen.add(key)
                unique_canonical.append(c)

        info = {
            "sources": sources,
            "all_aliases": all_aliases,
            "unrecognized": unrecognized,
            "resolved_count": len(unique_canonical),
            "taxonomy_version": self.version
        }

        return unique_canonical, info

    def get_canonical(self, test_level: TestLevel, **dims) -> 'CanonicalCheckID':
        """Get or create a canonical check ID."""
        canonical = CanonicalCheckID(
            test_level=test_level,
            domain=dims.get("domain"),
            protocol=dims.get("protocol"),
            technique=dims.get("technique"),
            validation_intent=dims.get("validation_intent"),
            taxonomy_version=self.version
        )
        key = str(canonical)
        if key not in self._canonical_cache:
            self._canonical_cache[key] = canonical
        return self._canonical_cache[key]

    def list_all_test_levels(self) -> List[str]:
        return [t.value for t in TestLevel]

    def list_all_domains(self) -> List[str]:
        return [d.value for d in Domain]

    def list_all_protocols(self) -> List[str]:
        return [p.value for p in Protocol]

    def list_all_techniques(self) -> List[str]:
        return [t.value for t in Technique]

    def list_all_intents(self) -> List[str]:
        return [i.value for i in ValidationIntent]

    def validate_canonical(self, canonical: 'CanonicalCheckID') -> bool:
        return canonical.taxonomy_version == self.version

    def get_taxonomy_info(self) -> Dict:
        return {
            "version": self.version,
            "dimensions": {
                "test_level": self.list_all_test_levels(),
                "domain": self.list_all_domains(),
                "protocol": self.list_all_protocols(),
                "technique": self.list_all_techniques(),
                "validation_intent": self.list_all_intents()
            },
            "alias_count": len(self.alias_registry.aliases),
            "canonical_count": len(self._canonical_cache)
        }


# ==============================================================================
# Global Instance
# ==============================================================================

TAXONOMY_REGISTRY = TaxonomyRegistry(version="1.0.0")

# ==============================================================================
# Serialization
# ==============================================================================

def save_taxonomy_registry(registry: TaxonomyRegistry, path: Path):
    """Save taxonomy registry to file."""
    data = {
        "version": registry.version,
        "aliases": {alias: str(canonical) for alias, canonical in registry.alias_registry.aliases.items()},
        "canonicals": [canonical.to_dict() for canonical in registry._canonical_cache.values()],
        "taxonomy_version": M1_TAXONOMY_VERSION.version,
        "taxonomy_released_at": M1_TAXONOMY_VERSION.released_at,
        "taxonomy_description": M1_TAXONOMY_VERSION.description
    }
    path.write_text(json.dumps(data, indent=2))

def load_taxonomy_registry(path: Path) -> TaxonomyRegistry:
    """Load taxonomy registry from file."""
    data = json.loads(path.read_text())
    registry = TaxonomyRegistry(version=data.get("version", "1.0.0"))
    return registry

# ==============================================================================
# Scope Normalization Functions
# ==============================================================================

def normalize_scope(
    cli_types: Optional[List[str]] = None,
    toml_types: Optional[List[str]] = None,
    nl_request: Optional[str] = None
) -> Tuple[List['CanonicalCheckID'], Dict]:
    """Normalize scope from three input channels into canonical CheckIDs."""
    return TAXONOMY_REGISTRY.parse_scope_input(cli_types, toml_types, nl_request)


def format_scope_for_display(canonical_checks: List['CanonicalCheckID'], info: Dict) -> str:
    lines = []

    if canonical_checks:
        lines.append("--- Included Checks ---")
        for check in canonical_checks:
            check_str = str(check)
            lines.append(f"  ✓ {check_str}")

    if info.get("unrecognized"):
        lines.append("")
        lines.append("--- Unrecognized Types ---")
        for u in info["unrecognized"]:
            lines.append(f"  ⨀ {u}: unrecognized")

    lines.append("")
    lines.append("--- Scope Summary ---")
    lines.append(f"  {len(canonical_checks)} check(s) included")
    lines.append(f"  Sources: {', '.join(info.get('sources', {}).keys())}")
    lines.append(f"  Taxonomy version: {info.get('taxonomy_version', 'unknown')}")

    return "\n".join(lines)


# ==============================================================================
# CLI Integration
# ==============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "info":
            info = TAXONOMY_REGISTRY.get_taxonomy_info()
            print(json.dumps(info, indent=2))
        elif sys.argv[1] == "parse":
            # Parse scope from args
            cli_types = sys.argv[2:] if len(sys.argv) > 2 else []
            canonical, info = TAXONOMY_REGISTRY.parse_scope_input(cli_types=cli_types)
            print("Resolved canonical IDs:")
            for c in canonical:
                print(f"  {c}")
            print(f"\nInfo: {json.dumps(info, indent=2)}")
        elif sys.argv[1] == "levels":
            print("Test Levels:", ", ".join(TAXONOMY_REGISTRY.list_all_test_levels()))
        elif sys.argv[1] == "domains":
            print("Domains:", ", ".join(TAXONOMY_REGISTRY.list_all_domains()))
        else:
            print("Usage: python -m asta.taxonomy [info|parse|levels|domains] [types...]")
    else:
        # Print taxonomy info
        info = TAXONOMY_REGISTRY.get_taxonomy_info()
        print(json.dumps(info, indent=2))