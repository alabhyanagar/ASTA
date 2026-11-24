#!/usr/bin/env python3
"""
ASTA M1 Scope Normalization Module

Normalizes scope input from three channels (CLI flags, TOML config, natural language)
into canonical CheckIDs with alias resolution and unrecognized handling.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path
import json

# Import from taxonomy
from asta.taxonomy import (
    CanonicalCheckID, TestLevel, TAXONOMY_REGISTRY,
    normalize_scope as taxonomy_normalize_scope
)

# ==============================================================================
# Scope Normalization Functions (re-export from taxonomy)
# ==============================================================================

normalize_scope = taxonomy_normalize_scope

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
# CLI Integration Functions
# ==============================================================================

def normalize_scope_input(
    cli_types: Optional[List[str]] = None,
    toml_types: Optional[List[str]] = None,
    nl_request: Optional[str] = None
) -> Tuple[List['CanonicalCheckID'], Dict]:
    """Main entry point for scope normalization from three channels."""
    from asta.taxonomy import TAXONOMY_REGISTRY
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
    from asta.taxonomy import CanonicalCheckID, TestLevel

    if len(sys.argv) > 1:
        if sys.argv[1] == "normalize":
            # Parse scope from args
            cli_types = sys.argv[2:] if len(sys.argv) > 2 else []
            canonical, info = normalize_scope_input(cli_types=cli_types)
            print("Resolved canonical IDs:")
            for c in canonical:
                print(f"  {c}")
            print(f"\nInfo: {json.dumps(info, indent=2)}")
        else:
            print("Usage: python -m asta.scope [normalize] [types...]")
    else:
        from asta.taxonomy import TAXONOMY_REGISTRY
        info = TAXONOMY_REGISTRY.get_taxonomy_info()
        print(json.dumps(info, indent=2))