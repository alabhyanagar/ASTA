import json
import jsonschema
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict

# ASTA TOML v1.0 JSON Schema draft-07
ASTA_TOML_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "asta.toml Configuration",
    "type": "object",
    "required": ["project", "scope", "execution"],
    "properties": {
        "project": {
            "type": "object",
            "required": ["name", "source"],
            "properties": {
                "name": {"type": "string"},
                "source": {"type": "string", "format": "path"}
            }
        },
        "scope": {
            "type": "object",
            "required": ["types", "risk_approval"],
            "properties": {
                "types": {"type": "array", "items": {"type": "string"}},
                "risk_approval": {"type": "string", "enum": ["low", "medium", "high", "critical"]}
            }
        },
        "execution": {
            "type": "object",
            "required": ["timeout_seconds", "max_workers"],
            "properties": {
                "timeout_seconds": {"type": "integer", "minimum": 60, "maximum": 86400},
                "max_workers": {"type": "integer", "minimum": 1, "maximum": 1}
            }
        },
        "dependencies": {
            "type": "object",
            "properties": {
                "pytest": {"type": "string"},
                "requests": {"type": "string"},
                "schemathesis": {"type": "string"},
                "httpx": {"type": "string"}
            }
        },
        "credentials": {
            "type": "object",
            "properties": {
                "reference": {"type": "string"}
            }
        }
    },
    "additionalProperties": False
}

@dataclass
class ValidationError:
    """Represents a validation error with field-level location."""
    message: str
    path: list = field(default_factory=list)
    field: str = None

    def __str__(self):
        if self.path:
            path_str = " -> ".join(str(p) for p in self.path)
            return f"[{path_str}] {self.message}"
        return self.message

@dataclass
class ValidationResult:
    """Result of config validation."""
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


class TOMLValidator:
    """Main validator for asta.toml configuration."""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.result = ValidationResult()
        self.config: dict = None

    def load_config(self) -> bool:
        """Load and parse the TOML config file."""
        try:
            with open(self.config_path, 'r') as f:
                # Simplified: in production, use tomllib (Python 3.11+) or toml package
                # For M1, we use JSON parsing as subset of TOML
                content = f.read()
                self.config = json.loads(content)
            return True
        except json.JSONDecodeError as e:
            self.result.errors.append(f"Invalid JSON: {e.message}")
            self.config = None
            return False

    def validate_schema(self) -> bool:
        """Validate config against JSON Schema draft-07."""
        if self.config is None:
            return False

        try:
            jsonschema.validate(instance=self.config, schema=ASTA_TOML_SCHEMA)
        except jsonschema.ValidationError as e:
            path_parts = list(e.path) if e.path else []
            self.result.errors.append(f"Schema validation error: {e.message} at {e.absolute_path}")
            return False

        return True

    def validate_business_rules(self) -> bool:
        """Validate business rules beyond schema."""
        if self.config is None:
            return False

        cfg = self.config

        # Rule 1: Config cannot broaden runtime safety policy
        execution = cfg.get("execution", {})
        timeout = execution.get("timeout_seconds", 300)
        max_workers = execution.get("max_workers", 1)

        if timeout > 300:
            self.result.errors.append(f"timeout_seconds={timeout} exceeds M1 limit of 300s; config cannot broaden runtime safety policy")

        if max_workers > 1:
            self.result.errors.append(f"max_workers={max_workers} exceeds M1 limit of 1 worker; config cannot broaden runtime safety policy")

        # Rule 2: Scope types must be from approved taxonomy
        scope = cfg.get("scope", {})
        user_types = scope.get("types", [])
        approved_types = ["unit", "integration", "api", "regression", "system", "functional"]

        for t in user_types:
            if t not in approved_types:
                self.result.errors.append(f"Scope type '{t}' not in approved taxonomy: {', '.join(approved_types)}")

        # Rule 3: risk_approval must be valid enum
        risk_approval = scope.get("risk_approval", "")
        valid_risks = ["low", "medium", "high", "critical"]
        if risk_approval not in valid_risks:
            self.result.errors.append(f"risk_approval='{risk_approval}' not in valid values: {', '.join(valid_risks)}")

        return len(self.result.errors) == 0

    def validate(self) -> dict:
        """Run full validation: schema + business rules."""
        self.load_config()
        self.validate_schema()
        self.validate_business_rules()
        return self.result


def validate_config(config_path: Path) -> List[str]:
    """Top-level validation function — returns list of error strings."""
    validator = TOMLValidator(config_path)
    result = validator.validate()

    errors = []
    for err in result.errors:
        errors.append(str(err))
    for warn in result.warnings:
        errors.append(f"WARNING: {warn}")

    return errors


def can_run_with_config(config_path: Path) -> bool:
    """Check if ASTA can run with given config."""
    errors = validate_config(config_path)
    return len(errors) == 0