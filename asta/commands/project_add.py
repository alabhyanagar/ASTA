#!/usr/bin/env python3
"""
ASTA M1 Project Add Command
"""

import click
from asta.models import project_add_command

@click.command(name='add', help='Create project from enabled local folder')
@click.argument('path', type=click.Path(exists=True))
def project_add(path):
    """Create project from enabled local folder.

    \b
    Examples:
        asta project add /path/to/project
        sta project add C:\\\\Users\\\\dev\\\\my-project
    """
    try:
        project = project_add_command(path)
        click.echo(f"✓ Project created: {project.name}")
        click.echo(f"  Source: {project.source_path}")
        click.echo(f"  Type: {project.profile.detected_type.value}")
        click.echo(f"  Scope: {', '.join(project.scope.types)}")
        click.echo(f"  Risk approval required: {project.scope.risk_approval}")
    except Exception as e:
        click.echo(f"Error: {e}")
        exit(1)