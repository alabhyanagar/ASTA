#!/usr/bin/env python3
"""
ASTA M1 Inspect Command
"""

import click
from asta.inspection import inspect_project

@click.command('inspect', help='Inspect project profile')
@click.argument('path', type=click.Path(exists=True), required=False)
def sta_inspect(path):
    """Inspect project profile without executing project modules.

    \b
    Examples:
        sta inspect /path/to/project
        sta inspect
    """
    from asta.inspection import inspect_project

    if path is None:
        path = click.prompt('Project path', type=click.Path(exists=True))

    # Detect project profile (deterministic, no module import)
    result = inspect_project(path)

    click.echo(f"--- Project Profile ---")
    click.echo(f"Path: {result.project_path}")

    # Language facts
    lang_facts = result.get_facts_by_category("language")
    for fact in lang_facts:
        if fact.name == "primary":
            click.echo(f"Detected type: {fact.value}")
            click.echo(f"Language: {fact.name}")

    # Frameworks
    fw_facts = result.get_facts_by_category("framework")
    if fw_facts:
        click.echo(f"Frameworks: {', '.join(f.name for f in fw_facts)}")

    # Manifests
    manifest_facts = result.get_facts_by_category("manifest")
    if manifest_facts:
        click.echo(f"Manifests found: {', '.join(f.name for f in manifest_facts)}")

    # Build commands
    build_facts = result.get_facts_by_category("build_command")
    if build_facts:
        click.echo(f"Build commands: {', '.join(f.name for f in build_facts)}")

    # Test commands
    test_facts = result.get_facts_by_category("test_command")
    if test_facts:
        click.echo(f"Test commands: {', '.join(f.name for f in test_facts)}")

    # Dependencies
    dep_facts = result.get_facts_by_category("dependency")
    if dep_facts:
        click.echo(f"Dependencies: {', '.join(f.name for f in dep_facts)}")

    # Confidence
    for fact in lang_facts:
        if fact.name == "primary":
            click.echo(f"Confidence: {fact.confidence.value}")

    # Show unknown facts
    if result.unknown_facts:
        click.echo("")
        click.echo("--- Unknown (remain unknown) ---")
        for fact in result.unknown_facts:
            click.echo(f"  • {fact}")