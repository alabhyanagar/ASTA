#!/usr/bin/env python3
"""
ASTA M1 Taxonomy Tests
"""

import pytest
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from asta.taxonomy import (
    TestLevel, Domain, Protocol, Technique, ValidationIntent,
    CanonicalCheckID, AliasRegistry, TaxonomyRegistry,
    M1_TAXONOMY_VERSION, TAXONOMY_REGISTRY
)


class TestDimensionEnums:
    """Test dimension enum values."""

    def test_test_levels(self):
        """Test level enum has expected values."""
        levels = [t.value for t in TestLevel]
        assert "unit" in levels
        assert "integration" in levels
        assert "api" in levels
        assert "regression" in levels
        assert "security" in levels
        assert "performance" in levels

    def test_domains(self):
        """Domain enum has expected values."""
        domains = [d.value for d in Domain]
        assert "backend" in domains
        assert "frontend" in domains
        assert "microservice" in domains
        assert "database" in domains

    def test_protocols(self):
        """Protocol enum has expected values."""
        protocols = [p.value for p in Protocol]
        assert "http" in protocols
        assert "grpc" in protocols
        assert "websocket" in protocols
        assert "graphql" in protocols

    def test_techniques(self):
        """Technique enum has expected values."""
        techniques = [t.value for t in Technique]
        assert "unit_test" in techniques
        assert "integration_test" in techniques
        assert "api_test" in techniques
        assert "security_test" in techniques
        assert "fuzz_test" in techniques

    def test_validation_intents(self):
        """Validation intent enum has expected values."""
        intents = [i.value for i in ValidationIntent]
        assert "functional_correctness" in intents
        assert "performance" in intents
        assert "security" in intents
        assert "reliability" in intents


class TestCanonicalCheckID:
    """Test canonical check ID."""

    def test_basic_creation(self):
        """Create basic canonical ID."""
        canonical = CanonicalCheckID(test_level=TestLevel.UNIT)

        assert canonical.test_level == TestLevel.UNIT
        assert canonical.domain is None
        assert canonical.protocol is None
        assert canonical.technique is None
        assert canonical.validation_intent is None
        assert canonical.taxonomy_version == "1.0.0"

    def test_full_creation(self):
        """Create canonical ID with all dimensions."""
        canonical = CanonicalCheckID(
            test_level=TestLevel.API,
            domain=Domain.BACKEND,
            protocol=Protocol.HTTPS,
            technique=Technique.API_TEST,
            validation_intent=ValidationIntent.CONTRACT_COMPLIANCE
        )

        assert canonical.test_level == TestLevel.API
        assert canonical.domain == Domain.BACKEND
        assert canonical.protocol == Protocol.HTTPS
        assert canonical.technique == Technique.API_TEST
        assert canonical.validation_intent == ValidationIntent.CONTRACT_COMPLIANCE

    def test_string_representation(self):
        """String representation includes all dimensions."""
        canonical = CanonicalCheckID(
            test_level=TestLevel.UNIT,
            domain=Domain.LIBRARY,
            technique=Technique.UNIT_TEST
        )

        s = str(canonical)
        assert "test_level=unit" in s
        assert "domain=library" in s
        assert "technique=unit_test" in s

    def test_tags(self):
        """Get flat tag list."""
        canonical = CanonicalCheckID(
            test_level=TestLevel.API,
            domain=Domain.BACKEND,
            protocol=Protocol.HTTPS,
            technique=Technique.API_TEST,
            validation_intent=ValidationIntent.CONTRACT_COMPLIANCE
        )

        tags = canonical.get_tags()
        assert tags == ["api", "backend", "https", "api_test", "contract_compliance"]

    def test_matches_scope(self):
        """Check scope matching."""
        canonical = CanonicalCheckID(test_level=TestLevel.UNIT)
        assert canonical.matches_scope(["unit", "integration"]) == True
        assert canonical.matches_scope(["integration", "api"]) == False

    def test_to_dict(self):
        """Convert to dict."""
        canonical = CanonicalCheckID(
            test_level=TestLevel.INTEGRATION,
            domain=Domain.MICROSERVICE,
            protocol=Protocol.GRPC
        )

        data = canonical.to_dict()

        assert data["test_level"] == "integration"
        assert data["domain"] == "microservice"
        assert data["protocol"] == "grpc"
        assert data["technique"] is None
        assert data["validation_intent"] is None
        assert data["taxonomy_version"] == "1.0.0"

    def test_from_dict(self):
        """Create from dict."""
        data = {
            "test_level": "api",
            "domain": "backend",
            "protocol": "https",
            "technique": "api_test",
            "validation_intent": "contract_compliance",
            "taxonomy_version": "1.0.0"
        }

        canonical = CanonicalCheckID.from_dict(data)

        assert canonical.test_level == TestLevel.API
        assert canonical.domain == Domain.BACKEND
        assert canonical.protocol == Protocol.HTTPS
        assert canonical.technique == Technique.API_TEST
        assert canonical.validation_intent == ValidationIntent.CONTRACT_COMPLIANCE

    def test_hashable(self):
        """Canonical IDs are hashable and can be used in sets."""
        c1 = CanonicalCheckID(test_level=TestLevel.UNIT)
        c2 = CanonicalCheckID(test_level=TestLevel.UNIT)
        c3 = CanonicalCheckID(test_level=TestLevel.INTEGRATION)

        s = {c1, c2, c3}
        assert len(s) == 2  # c1 and c2 are equal


class TestAliasRegistry:
    """Test alias registry."""

    def test_resolve_test_level_aliases(self):
        """Resolve test level aliases."""
        registry = AliasRegistry.create_v1()

        # Test level aliases
        assert registry.resolve("unit") is not None
        assert registry.resolve("unit").test_level == TestLevel.UNIT
        assert registry.resolve("pyunit") is not None
        assert registry.resolve("pyunit").test_level == TestLevel.UNIT
        assert registry.resolve("integration") is not None
        assert registry.resolve("integration").test_level == TestLevel.INTEGRATION
        assert registry.resolve("api") is not None
        assert registry.resolve("api").test_level == TestLevel.API
        assert registry.resolve("regression") is not None
        assert registry.resolve("regression").test_level == TestLevel.REGRESSION
        assert registry.resolve("security") is not None
        assert registry.resolve("security").test_level == TestLevel.SECURITY

    def test_resolve_domain_aliases(self):
        """Resolve domain aliases."""
        registry = AliasRegistry.create_v1()

        # Domain aliases combine test level + domain
        backend = registry.resolve("backend")
        assert backend is not None
        assert backend.test_level == TestLevel.API
        assert backend.domain == Domain.BACKEND

        frontend = registry.resolve("frontend")
        assert frontend is not None
        assert frontend.test_level == TestLevel.SYSTEM
        assert frontend.domain == Domain.FRONTEND

        microservice = registry.resolve("microservice")
        assert microservice is not None
        assert microservice.domain == Domain.MICROSERVICE

    def test_resolve_technique_aliases(self):
        """Resolve technique aliases."""
        registry = AliasRegistry.create_v1()

        unit_test = registry.resolve("unit_test")
        assert unit_test is not None
        assert unit_test.technique == Technique.UNIT_TEST

        integration_test = registry.resolve("integration_test")
        assert integration_test is not None
        assert integration_test.technique == Technique.INTEGRATION_TEST

        api_test = registry.resolve("api_test")
        assert api_test is not None
        assert api_test.technique == Technique.API_TEST

        fuzz_test = registry.resolve("fuzz_test")
        assert fuzz_test is not None
        assert fuzz_test.technique == Technique.FUZZ_TEST

    def test_resolve_intent_aliases(self):
        """Resolve validation intent aliases."""
        registry = AliasRegistry.create_v1()

        functional = registry.resolve("functional")
        assert functional is not None
        assert functional.validation_intent == ValidationIntent.FUNCTIONAL_CORRECTNESS

        performance = registry.resolve("performance")
        assert performance is not None
        assert performance.validation_intent == ValidationIntent.PERFORMANCE

        security = registry.resolve("security")
        assert security is not None
        # security resolves to test level SECURITY (from test_level_aliases)
        assert security.test_level == TestLevel.SECURITY

    def test_resolve_many(self):
        """Resolve multiple aliases at once."""
        registry = AliasRegistry.create_v1()

        canonical, unrecognized = registry.resolve_many(["unit", "integration", "unknown_type"])

        assert len(canonical) == 2
        assert {c.test_level for c in canonical} == {TestLevel.UNIT, TestLevel.INTEGRATION}
        assert unrecognized == ["unknown_type"]

    def test_deduplication(self):
        """Duplicate types across channels are deduplicated."""
        registry = AliasRegistry.create_v1()

        canonical, info = registry.resolve_many(["unit", "integration"], ["unit", "api"])

        assert len(canonical) == 3  # unit, integration, api
        levels = {c.test_level for c in canonical}
        assert levels == {TestLevel.UNIT, TestLevel.INTEGRATION, TestLevel.API}

    def test_get_canonical(self):
        """Get or create canonical ID."""
        canonical = TAXONOMY_REGISTRY.get_canonical(
            TestLevel.UNIT,
            domain=Domain.LIBRARY,
            technique=Technique.UNIT_TEST
        )

        assert canonical.test_level == TestLevel.UNIT
        assert canonical.domain == Domain.LIBRARY
        assert canonical.technique == Technique.UNIT_TEST

    def test_list_dimensions(self):
        """List all dimension values."""
        assert "unit" in TAXONOMY_REGISTRY.list_all_test_levels()
        assert "backend" in TAXONOMY_REGISTRY.list_all_domains()
        assert "https" in TAXONOMY_REGISTRY.list_all_protocols()
        assert "unit_test" in TAXONOMY_REGISTRY.list_all_techniques()
        assert "functional_correctness" in TAXONOMY_REGISTRY.list_all_intents()

    def test_taxonomy_info(self):
        """Get complete taxonomy info."""
        info = TAXONOMY_REGISTRY.get_taxonomy_info()

        assert info["version"] == "1.0.0"
        assert "test_level" in info["dimensions"]
        assert "domain" in info["dimensions"]
        assert "protocol" in info["dimensions"]
        assert "technique" in info["dimensions"]
        assert "validation_intent" in info["dimensions"]
        assert len(info["dimensions"]["test_level"]) > 10


class TestTaxonomyVersioning:
    """Test taxonomy versioning."""

    def test_m1_taxonomy_version(self):
        """M1 taxonomy version is set."""
        assert M1_TAXONOMY_VERSION.version == "1.0.0"
        assert M1_TAXONOMY_VERSION.released_at == "2026-11-23T00:00:00Z"

    def test_canonical_has_version(self):
        """Canonical IDs include taxonomy version."""
        canonical = CanonicalCheckID(test_level=TestLevel.UNIT)
        assert canonical.taxonomy_version == "1.0.0"


class TestSerialization:
    """Test taxonomy serialization."""

    def test_registry_serialization(self):
        """Registry can be serialized."""
        registry = TaxonomyRegistry(version="1.0.0")
        info = registry.get_taxonomy_info()

        # Should be JSON serializable
        json_str = json.dumps(info)
        assert "test_level" in json_str
        assert "domain" in json_str

    def test_canonical_serialization(self):
        """Canonical ID serializes correctly."""
        canonical = CanonicalCheckID(
            test_level=TestLevel.API,
            domain=Domain.BACKEND,
            protocol=Protocol.HTTPS,
            technique=Technique.API_TEST,
            validation_intent=ValidationIntent.CONTRACT_COMPLIANCE
        )

        data = canonical.to_dict()
        assert data["test_level"] == "api"
        assert data["domain"] == "backend"
        assert data["protocol"] == "https"
        assert data["technique"] == "api_test"
        assert data["validation_intent"] == "contract_compliance"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])