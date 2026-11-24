import json
import jsonschema
from pathlib import Path
from typing import List

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

def validate_config(config_path: Path) -> List[str]:
    """Validate asta.toml configuration against schema.

    Returns list of error strings; empty list = valid.
    """
    errors = []

    if not config_path.exists():
        errors.append(f"Configuration file not found: {config_path}")
        return errors

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)

        try:
            jsonschema.validate(instance=config, schema=ASTA_TOML_SCHEMA)
        except jsonschema.ValidationError as e:
            path_parts = list(e.path) if e.path else []
            errors.append(f"Schema validation error: {e.message} at {e.absolute_path}")
        return errors
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON in configuration: {e.message}")
        return errors


def can_run_with_config(config_path: Path) -> bool:
    """Check if ASTA can run with given config."""
    errors = validate_config(config_path)
    return len(errors) == 0