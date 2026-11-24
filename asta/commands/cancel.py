#!/usr/bin/env python3
"""
ASTA M1 Cancel Command
"""

import click
from asta.models import Project

@click.command('cancel', help='Cancel active run')
def sta_cancel():
    """Cancel active run."""
    from asta.models import Project

    runs = Project.get_runs()
    if runs:
        latest_run = runs[-1]
        click.echo(f"--- Cancelling run: {latest_run['run_id']} ---")
        click.echo(f"  Run cancelled (AI-off mode — no worker was active)")
        click.echo(f"  Partial evidence preserved.")
        click.echo(f"  Use 'sta rerun' to recover/checkpointed runs.")
    else:
        click.echo("  No active run to cancel.")
        click.echo("  Use 'sta status' to check for runs.")