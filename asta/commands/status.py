#!/usr/bin/env python3
"""
ASTA M1 Status Command
"""

import click
from asta.models import Project

@click.command('status', help='Show run state')
def sta_status():
    """Show current run state."""
    from asta.models import Project

    # Check for existing run state
    runs = Project.get_runs()
    if runs:
        latest_run = runs[-1]  # Most recent run
        click.echo(f"--- Run State ---")
        click.echo(f"  Run ID: {latest_run['run_id']}")
        click.echo(f"  Status: {latest_run['status']}")
        click.echo(f"  Started: {latest_run['started']}")
        click.echo(f"  Completed: {latest_run['completed']}")
        click.echo(f"  Checks: {latest_run['checks_total']} total")
        click.echo(f"  Passed: {latest_run['passed_count']}")
        click.echo(f"  Failed: {latest_run['failed_count']}")
        click.echo(f"  Blocked: {latest_run['blocked_count']}")
        click.echo(f"  Unsupported: {latest_run['unsupported_count']}")
    else:
        click.echo(f"--- Run State ---")
        click.echo(f"  No active runs found.")
        click.echo(f"  Use 'asta project add' to start a new project.")
        click.echo(f"  Use 'sta plan' to create a plan.")
        click.echo(f"  Runs are tracked in the project workspace.")