"""
ASTA — Autonomous Software Testing Platform
CLI-first, locally installed software testing application.

M1: Local CLI for Windows developers using WSL2 and Docker.
All operations AI-off by default. Deterministic verdicts from evidence.
"""

__version__ = "1.0.0"

# Public API exports
from .cli import cli
from .schema import ASTA_TOML_SCHEMA, validate_config, can_run_with_config
from .toml_validator import TOMLValidator, ValidationResult, ValidationError
from .commands.project_add import project_add
from .commands.inspect import sta_inspect
from .commands.plan import sta_plan
from .commands.approve import sta_approve
from .commands.run import sta_run
from .commands.status import sta_status
from .commands.cancel import sta_cancel
from .commands.rerun import sta_rerun
from .commands.report import sta_report