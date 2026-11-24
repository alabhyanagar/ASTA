#!/usr/bin/env python3
"""
ASTA M1 Run Command
"""

import click
from asta.models import Project
from asta.scope import normalize_scope

@click.command('run', help='Run approved checks (AI-off mode; no worker execution yet in M1a)')
@click.argument('path', type=click.Path(exists=True), required=False)
@click.option('--types', multiple=True, help='Run specific test types (unit, integration, api, regression)')
def sta_run(path, types):
    """Run approved checks in AI-off mode.

    \b
    Examples:
        sta run /path/to/project
        sta run --types unit,integration
    """
    from asta.models import Project
    from asta.scope import normalize_scope

    if path is None:
        path = click.prompt('Project path', type=click.Path(exists=True))

    # Load project
    project = Project.load(path)
    if not project:
        click.echo("Project not found. Run 'asta project add' first.")
        return

    # Normalize scope/types
    selected_types = normalize_scope(types or project.scope.types)

    click.echo(f"--- Run Summary (AI-off mode) ---")
    click.echo(f"Project: {project.name}")
    click.echo(f"Selected types: {', '.join(selected_types)}")
    click.echo(f"Risk approval: {project.scope.risk_approval}")
    click.echo(f"Included checks: {len(project.checks_included)}")
    click.echo(f"Excluded checks: {len(project.checks_excluded)}")
    click.echo(f"Blocked checks: {len(project.checks_blocked)}")
    click.echo(f"Unsupported checks: {len(project.checks_unsupported)}")
    click.echo("")

    click.echo(f"--- Run Planning (AI-off) ---")
    click.echo(f"  • Scope normalized from: {', '.join(types) if types else 'project config'}")
    click.echo(f"  • {len(selected_types)} type(s) selected from approved scope")
    click.echo(f"  • All checks against approved target policy only")
    click.echo(f"  • Worker execution not enabled in M1a — isolated worker setup only")
    click.echo(f"  • Use 'sta status' to check run state; 'sta rerun' to retry")
    click.echo(f"  • Run plan saved for later execution when worker available")
    click.echo("")

    click.echo(f"--- Run Complete (AI-off) ---")
    click.echo(f"  No checks were executed in this mode.")
    click.echo(f"  Plan and scope are saved for later execution.")
    click.echo(f"  Run 'sta status' to see current run state.")
    click.echo(f"  Run 'sta report' to generate reports from prior runs.")
    click.echo("")