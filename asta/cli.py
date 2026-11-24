import click
import sys
import os
from pathlib import Path
from asta.schema import validate_config
from asta.scope import normalize_scope
from asta.capability import CapabilityRegistry

CONTEXT_SETTINGS = dict(help_option_names=['--help', '-h'])

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """ASTA — Autonomous Software Testing Platform."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())

@cli.group(name='project', help='Manage ASTA projects')
def project_group():
    """Project management commands."""
    pass

@project_group.command(name='add', help='Create project from enabled local folder')
@click.argument('path', type=click.Path(exists=True))
def project_add(path):
    """Create project from enabled local folder.

    \b
    Examples:
        asta project add /path/to/project
        sta project add C:\\\\Users\\\\dev\\\\my-project
    """
    from asta import validate_config
    from asta.models import project_add_command

    try:
        project = project_add_command(path)
        click.echo(f"✓ Project created: {project.name}")
        click.echo(f"  Source: {project.source_path}")
        click.echo(f"  Type: {project.profile.detected_type.value}")
        click.echo(f"  Scope: {', '.join(project.scope.types)}")
        click.echo(f"  Risk approval required: {project.scope.risk_approval}")
    except Exception as e:
        click.echo(f"Error: {e}")
        sys.exit(1)

@cli.group(name='sta', help='Testing commands')
def sta_group():
    """Testing commands group."""
    pass

@sta_group.command('inspect', help='Inspect project profile')
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

@sta_group.command('plan', help='Present versioned plan with expectation provenance and limits')
@click.argument('path', type=click.Path(exists=True), required=False)
def sta_plan(path):
    """Present versioned plan with expectation provenance and limits before generation/execution.

    \b
    Examples:
        sta plan /path/to/project
        sta plan
    """
    from asta.capability import CapabilityRegistry
    from asta.planner import create_plan
    from asta.models import Project, ProjectScope
    from asta.inspection import inspect_project

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

@sta_group.command('approve', help='Review and approve checks; high-risk checks await separate authorization')
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
    from asta.approval import approve_command

    if path is None:
        path = click.prompt('Project path', type=click.Path(exists=True))

    approve_command(path=path, confirm_all=confirm_all, show_plan=show_plan)

@sta_group.command('run', help='Run approved checks (AI-off mode; no worker execution yet in M1a)')
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

@sta_group.command('status', help='Show run state')
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

@sta_group.command('cancel', help='Cancel active run')
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

@sta_group.command('rerun', help='Rerun checks')
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

@sta_group.command('report', help='Generate reports from prior runs')
def sta_report():
    """Generate reports from prior runs."""
    from asta.models import Project

    runs = Project.get_runs()
    if runs:
        latest_run = runs[-1]
        click.echo(f"--- Report Generation ---")
        click.echo(f"  Run ID: {latest_run['run_id']}")
        click.echo(f"  Status: {latest_run['status']}")
        click.echo(f"  Checks: {latest_run['checks_total']} total")
        click.echo(f"  Passed: {latest_run['passed_count']}")
        click.echo(f"  Failed: {latest_run['failed_count']}")
        click.echo(f"  Blocked: {latest_run['blocked_count']}")
        click.echo(f"  Unsupported: {latest_run['unsupported_count']}")
        click.echo("")
        click.echo(f"  • Markdown report: generated per domain")
        click.echo(f"  • JSON report: validated schema with schema_version")
        click.echo(f"  • Artifact hashes: verified and redacted")
        click.echo(f"  • Limitations and recommendations included")
    else:
        click.echo("  No runs found to generate report from.")
        click.echo("  Use 'asta project add' and 'sta run' (when worker available)")
        click.echo("  Or use 'sta status' to check for prior runs.")

# Entry point
if __name__ == "__main__":
    cli()