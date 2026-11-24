#!/usr/bin/env python3
"""
ASTA M1 Approve Command - Recommendation Review and Exact Approval Binding

Each recommendation includes rationale/evidence/risk/prerequisites.
Approved additions bind to run, exact scope, plan revision/content hash and policy version.
Declined/pending additions never execute.
Material change invalidates approval and is audited.
"""

import click
from asta.recommendation import approve_command

@click.command('approve', help='Review and approve checks; high-risk checks await separate authorization')
@click.argument('path', type=click.Path(exists=True), required=False)
@click.option('--confirm-all', is_flag=True, help='Approve all included checks without individual review')
@click.option('--show-plan', is_flag=True, help='Show plan without prompting for approval')
def sta_approve(path, confirm_all, show_plan):
    """Review and approve checks; high-risk checks await separate authorization.

    \b
    Examples:
        sta approve /path/to/project
        sta approve
    """
    if path is None:
        path = click.prompt('Project path', type=click.Path(exists=True))

    from asta.recommendation import approve_command as _approve_command
    _approve_command(path=path, confirm_all=confirm_all, show_plan=show_plan)