#!/usr/bin/env python3
"""
ASTA M1 Rerun Command
"""

import click
from asta.models import Project

@click.command('rerun', help='Rerun checks')
@click.argument('path', type=click.Path(exists=True), required=False)
def sta_rerun(path):
    """Rerun checks."""
    from asta.models import Project

    if path is None:
        path = click.prompt('Project path', type=click.Path(exists=True))

    # Load project and check state
    project = Project.load(path)
    runs = Project.get_runs()

    if runs:
        latest_run = runs[-1]
        status = latest_run['status']
        click.echo(f"--- Rerun Summary ---")
        click.echo(f"  Project: {project.name}")
        click.echo(f"  Current run status: {status}")
        click.echo(f"  Previous attempts: {latest_run.get('attempt_count', 0)}")
        click.echo(f"  Rerun will preserve: attempt history, evidence, plan revision")
        click.echo("")
        click.echo(f"  Rerun planning (AI-off):")
        click.echo(f"  • Scope from: {latest_run.get('scope', 'project config')}")
        click.echo(f"  • {len(project.checks_included)} checks included in prior plan")
        click.echo(f"  • Ready to rerun when worker available")
    else:
        click.echo("  No prior runs found.")
        click.echo("  Use 'sta plan' to create a plan first.")

    click.echo("")
    click.echo(f"  Rerun planning (AI-off):")
    click.echo(f"  • Scope: {', '.join(project.scope.types)}")
    click.echo(f"  • Ready to plan and execute when worker available")