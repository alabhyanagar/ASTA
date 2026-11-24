#!/usr/bin/env python3
"""
ASTA M1 Plan Command
"""

import click
from asta.capability import CapabilityRegistry
from asta.planner import create_plan
from asta.models import Project, ProjectScope
from asta.inspection import inspect_project

@click.command('plan', help='Present versioned plan with expectation provenance and limits')
@click.argument('path', type=click.Path(exists=True), required=False)
def sta_plan(path):
    """Present versioned plan with expectation provenance and limits before generation/execution.

    \b
    Examples:
        sta plan /path/to/project
        sta plan
    """
    if path is None:
        path = click.prompt('Project path', type=click.Path(exists=True))

    # Get project
    project = Project.load(path)
    if not project:
        click.echo("Project not found. Run 'asta project add' first.")
        return

    # Inspect
    facts = inspect_project(path)

    # Get scope and auth
    scope = project.scope
    auth = {"allowed_targets": [], "authorized_risks": []}

    # Create plan
    registry = CapabilityRegistry()
    plan = create_plan(project, facts.to_dict()["facts"], scope, auth, plan_revision=1)

    click.echo(f"--- Testing Plan ---")
    click.echo(f"Project: {plan.project_name}")
    click.echo(f"Plan Revision: {plan.plan_revision}")
    click.echo(f"Content Hash: {plan.content_hash[:12]}...")
    click.echo(f"Generated: {plan.generated_at}")
    click.echo(f"Scope Types: {', '.join(plan.scope_types)}")
    click.echo(f"Risk Approval: {plan.risk_approval}")
    click.echo(f"AI-Off: {plan.ai_off}")
    click.echo("")

    click.echo(f"--- Included Checks ---")
    for check in plan.get_included_checks():
        risk_marker = " ⚠ HIGH RISK" if check.risk_level in ["high", "critical"] else ""
        click.echo(f"  ✓ {check.key}: {check.title}{risk_marker}")
        click.echo(f"    Type: {check.test_type}")
        click.echo(f"    Risk: {check.risk_level}")
        if check.prerequisites:
            click.echo(f"    Prerequisites: {', '.join(check.prerequisites)}")
        if check.target:
            click.echo(f"    Target: {check.target}")
        click.echo("")

    click.echo(f"--- Excluded Checks ---")
    for check in plan.get_excluded_checks():
        click.echo(f"  ⨉ {check.key}: {check.title}")
        click.echo(f"    Reason: {check.reason}")
        click.echo("")

    click.echo(f"--- Blocked Checks ---")
    for check in plan.get_blocked_checks():
        click.echo(f"  ⨀ {check.key}: {check.title}")
        click.echo(f"    Reason: {check.reason}")
        click.echo("")

    click.echo(f"--- Unsupported Checks ---")
    for check in plan.get_unsupported_checks():
        click.echo(f"  ⨀ {check.key}: {check.title}")
        click.echo(f"    Reason: {check.reason}")
        click.echo("")

    click.echo(f"--- Plan Provenance ---")
    click.echo(f"  Generated: {plan.provenance.generated_at}")
    click.echo(f"  Scope: {plan.provenance.scope_types}")
    click.echo(f"  Plan revision: {plan.provenance.plan_revision}")
    click.echo(f"  Content hash: {plan.provenance.content_hash}")
    click.echo(f"  AI-off: {plan.provenance.ai_off}")