#!/usr/bin/env python3
"""
ASTA M1 Data Models

Core data models for projects, runs, checks, and evidence.
All models are deterministic, serializable, and AI-off compatible.
"""

import json
import hashlib
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum

# ==============================================================================
# Enums
# ==============================================================================

class ProjectType(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    JAVA = "java"
    RUST = "rust"
    UNKNOWN = "unknown"

class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    NO_RESULT = "no_result"

class CheckStatus(str, Enum):
    PASSED = "Passed"
    FAILED = "Failed"
    FLAKY = "Flaky"
    SKIPPED = "Skipped"
    BLOCKED = "Blocked"
    INCONCLUSIVE = "Inconclusive"
    UNSUPPORTED = "Unsupported"
    ERROR = "Error"

# ==============================================================================
# Core Models
# ==============================================================================

@dataclass
class ProjectScope:
    """Project testing scope configuration."""
    types: List[str] = field(default_factory=list)
    risk_approval: str = "high"  # low, medium, high, critical

    def to_dict(self) -> Dict:
        return {"types": self.types, "risk_approval": self.risk_approval}

    @classmethod
    def from_dict(cls, data: Dict) -> 'ProjectScope':
        return cls(types=data.get("types", []), risk_approval=data.get("risk_approval", "high"))

@dataclass
class ProjectConfig:
    """Project execution configuration."""
    timeout_seconds: int = 300
    max_workers: int = 1

    def to_dict(self) -> Dict:
        return {"timeout_seconds": self.timeout_seconds, "max_workers": self.max_workers}

    @classmethod
    def from_dict(cls, data: Dict) -> 'ProjectConfig':
        return cls(
            timeout_seconds=data.get("timeout_seconds", 300),
            max_workers=data.get("max_workers", 1)
        )

@dataclass
class ProjectCredentials:
    """Project credential references (never stores actual secrets)."""
    reference: Optional[str] = None  # e.g., "os-keyring:my-secret"

    def to_dict(self) -> Dict:
        return {"reference": self.reference} if self.reference else {}

    @classmethod
    def from_dict(cls, data: Dict) -> 'ProjectCredentials':
        return cls(reference=data.get("reference"))

@dataclass
class ProjectDependencies:
    """Pinned project dependencies."""
    pytest: str = ">=8.2.0,<9.0.0"
    requests: str = "==2.32.3"
    schemathesis: str = "==5.6.0"
    httpx: str = "==0.27.0"

    def to_dict(self) -> Dict:
        return {
            "pytest": self.pytest,
            "requests": self.requests,
            "schemathesis": self.schemathesis,
            "httpx": self.httpx
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ProjectDependencies':
        return cls(
            pytest=data.get("pytest", ">=8.2.0,<9.0.0"),
            requests=data.get("requests", "==2.32.3"),
            schemathesis=data.get("schemathesis", "==5.6.0"),
            httpx=data.get("httpx", "==0.27.0")
        )

@dataclass
class ProjectProfile:
    """Detected project profile from static inspection."""
    detected_type: ProjectType = ProjectType.UNKNOWN
    language: str = "unknown"
    version: Optional[str] = None
    frameworks: List[str] = field(default_factory=list)
    manifests: List[str] = field(default_factory=list)
    build_commands: List[str] = field(default_factory=list)
    test_commands: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    confidence: float = 0.0  # 0.0 to 1.0
    unknown: List[str] = field(default_factory=list)  # Unknown facts with reasons

    def to_dict(self) -> Dict:
        return {
            "detected_type": self.detected_type.value,
            "language": self.language,
            "version": self.version,
            "frameworks": self.frameworks,
            "manifests": self.manifests,
            "build_commands": self.build_commands,
            "test_commands": self.test_commands,
            "dependencies": self.dependencies,
            "confidence": self.confidence,
            "unknown": self.unknown
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ProjectProfile':
        return cls(
            detected_type=ProjectType(data.get("detected_type", "unknown")),
            language=data.get("language", "unknown"),
            version=data.get("version"),
            frameworks=data.get("frameworks", []),
            manifests=data.get("manifests", []),
            build_commands=data.get("build_commands", []),
            test_commands=data.get("test_commands", []),
            dependencies=data.get("dependencies", []),
            confidence=data.get("confidence", 0.0),
            unknown=data.get("unknown", [])
        )

@dataclass
class Project:
    """ASTA Project - core entity for testing."""
    id: str
    name: str
    source_path: str
    created_at: str
    updated_at: str
    profile: ProjectProfile
    scope: ProjectScope
    config: ProjectConfig
    credentials: ProjectCredentials
    dependencies: ProjectDependencies
    checks_included: List[str] = field(default_factory=list)
    checks_excluded: List[str] = field(default_factory=list)
    checks_blocked: List[str] = field(default_factory=list)
    checks_unsupported: List[str] = field(default_factory=list)
    checks_awaiting_authorization: List[str] = field(default_factory=list)
    authorization_confirmed: bool = False
    ownership_confirmed: bool = False

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "source_path": self.source_path,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "profile": self.profile.to_dict(),
            "scope": self.scope.to_dict(),
            "config": self.config.to_dict(),
            "credentials": self.credentials.to_dict(),
            "dependencies": self.dependencies.to_dict(),
            "checks_included": self.checks_included,
            "checks_excluded": self.checks_excluded,
            "checks_blocked": self.checks_blocked,
            "checks_unsupported": self.checks_unsupported,
            "checks_awaiting_authorization": self.checks_awaiting_authorization,
            "authorization_confirmed": self.authorization_confirmed,
            "ownership_confirmed": self.ownership_confirmed
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Project':
        return cls(
            id=data["id"],
            name=data["name"],
            source_path=data["source_path"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            profile=ProjectProfile.from_dict(data["profile"]),
            scope=ProjectScope.from_dict(data["scope"]),
            config=ProjectConfig.from_dict(data["config"]),
            credentials=ProjectCredentials.from_dict(data.get("credentials", {})),
            dependencies=ProjectDependencies.from_dict(data.get("dependencies", {})),
            checks_included=data.get("checks_included", []),
            checks_excluded=data.get("checks_excluded", []),
            checks_blocked=data.get("checks_blocked", []),
            checks_unsupported=data.get("checks_unsupported", []),
            checks_awaiting_authorization=data.get("checks_awaiting_authorization", []),
            authorization_confirmed=data.get("authorization_confirmed", False),
            ownership_confirmed=data.get("ownership_confirmed", False)
        )

    def save(self, workspace_path: Path) -> None:
        """Save project to workspace."""
        project_dir = workspace_path / ".asta" / "projects" / self.id
        project_dir.mkdir(parents=True, exist_ok=True)

        project_file = project_dir / "project.json"
        project_file.write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, source_path: str, workspace_path: Path) -> Optional['Project']:
        """Load project from source path."""
        projects_dir = workspace_path / ".asta" / "projects"
        if not projects_dir.exists():
            return None

        for project_dir in projects_dir.iterdir():
            project_file = project_dir / "project.json"
            if project_file.exists():
                data = json.loads(project_file.read_text())
                if data.get("source_path") == source_path:
                    return cls.from_dict(data)

        return None

    @classmethod
    def create(cls, path: str, workspace_path: Path,
               scope_types: List[str] = None, risk_approval: str = "high",
               config: ProjectConfig = None, credentials: ProjectCredentials = None,
               dependencies: ProjectDependencies = None) -> 'Project':
        """Create a new project from source path."""
        path_obj = Path(path).resolve()

        if not path_obj.exists():
            raise ValueError(f"Source path does not exist: {path}")

        if not path_obj.is_dir():
            raise ValueError(f"Source path is not a directory: {path}")

        # Check if project already exists
        existing = cls.load(path, workspace_path)
        if existing:
            raise ValueError(f"Project already exists: {existing.id} ({existing.name})")

        # Generate project ID from path
        path_hash = hashlib.sha256(str(path_obj).encode()).hexdigest()[:12]
        project_id = f"proj_{path_hash}"

        # Detect profile
        profile = detect_project_profile(path_obj)

        # Get project name
        name = path_obj.name or "unnamed-project"

        # Create project
        now = datetime.utcnow().isoformat() + "Z"
        project = cls(
            id=project_id,
            name=name,
            source_path=str(path_obj),
            created_at=now,
            updated_at=now,
            profile=profile,
            scope=ProjectScope(types=scope_types or [], risk_approval=risk_approval),
            config=config or ProjectConfig(),
            credentials=credentials or ProjectCredentials(),
            dependencies=dependencies or ProjectDependencies(),
        )

        # Save to workspace
        project.save(workspace_path)

        return project

    def get_workspace(self, workspace_path: Path) -> Path:
        """Get project workspace directory."""
        return workspace_path / ".asta" / "projects" / self.id

    def get_runs_dir(self, workspace_path: Path) -> Path:
        """Get project runs directory."""
        return self.get_workspace(workspace_path) / "runs"

    def get_approvals_dir(self, workspace_path: Path) -> Path:
        """Get project approvals directory."""
        return self.get_workspace(workspace_path) / "approvals"

    def get_current_plan(self, workspace_path: Path) -> Optional['Plan']:
        """Get the current plan for this project."""
        from .planner import Plan
        runs_dir = self.get_runs_dir(workspace_path)
        if not runs_dir.exists():
            return None

        plan_files = sorted(runs_dir.glob("plan_*.json"))
        if not plan_files:
            return None

        latest_plan = plan_files[-1]
        data = json.loads(latest_plan.read_text())
        return Plan.from_dict(data)


# ==============================================================================
# Profile Detection
# ==============================================================================

def detect_project_profile(path: Path) -> ProjectProfile:
    """Detect project profile from static inspection (no module execution)."""
    profile = ProjectProfile()
    confidence_scores = []

    # Check for Python project
    python_indicators = {
        "pyproject.toml": 0.9,
        "setup.py": 0.8,
        "setup.cfg": 0.7,
        "requirements.txt": 0.6,
        "Pipfile": 0.7,
        "poetry.lock": 0.8,
    }

    for indicator, weight in python_indicators.items():
        if (path / indicator).exists():
            profile.detected_type = ProjectType.PYTHON
            profile.language = "python"
            confidence_scores.append(weight)
            profile.manifests.append(indicator)

    # Check for JavaScript/TypeScript
    js_indicators = {
        "package.json": 0.9,
        "pnpm-lock.yaml": 0.7,
        "yarn.lock": 0.7,
        "tsconfig.json": 0.6,
    }

    for indicator, weight in js_indicators.items():
        if (path / indicator).exists():
            if profile.detected_type == ProjectType.UNKNOWN:
                profile.detected_type = ProjectType.JAVASCRIPT
                profile.language = "javascript"
            confidence_scores.append(weight)
            profile.manifests.append(indicator)

    # TypeScript override
    if (path / "tsconfig.json").exists():
        profile.detected_type = ProjectType.TYPESCRIPT
        profile.language = "typescript"
        confidence_scores.append(0.8)
        profile.manifests.append("tsconfig.json")

    # Go
    if (path / "go.mod").exists():
        profile.detected_type = ProjectType.GO
        profile.language = "go"
        confidence_scores.append(0.9)
        profile.manifests.append("go.mod")

    # Java
    java_indicators = {
        "pom.xml": 0.9,
        "build.gradle": 0.8,
        "build.gradle.kts": 0.8,
    }
    for indicator, weight in java_indicators.items():
        if (path / indicator).exists():
            profile.detected_type = ProjectType.JAVA
            profile.language = "java"
            confidence_scores.append(weight)
            profile.manifests.append(indicator)

    # Rust
    if (path / "Cargo.toml").exists():
        profile.detected_type = ProjectType.RUST
        profile.language = "rust"
        confidence_scores.append(0.9)
        profile.manifests.append("Cargo.toml")

    # Set confidence as max of all scores
    profile.confidence = max(confidence_scores) if confidence_scores else 0.0

    # If no clear detection, mark unknown
    if profile.detected_type == ProjectType.UNKNOWN:
        profile.unknown.append("Project type could not be determined from manifests")

    # Detect frameworks for Python
    if profile.detected_type == ProjectType.PYTHON:
        _detect_python_frameworks(path, profile)

    # Detect test commands
    _detect_test_commands(path, profile)

    return profile

def _detect_python_frameworks(path: Path, profile: ProjectProfile):
    """Detect Python frameworks from project files."""
    # Check pyproject.toml
    pyproject = path / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text()
        frameworks = {
            "fastapi": "FastAPI",
            "django": "Django",
            "flask": "Flask",
            "starlette": "Starlette",
            "pytest": "pytest",
        }
        for key, name in frameworks.items():
            if key in content.lower():
                profile.frameworks.append(name)

    # Check requirements.txt
    reqs = path / "requirements.txt"
    if reqs.exists():
        content = reqs.read_text()
        frameworks = {
            "fastapi": "FastAPI",
            "django": "Django",
            "flask": "Flask",
            "requests": "Requests",
            "sqlalchemy": "SQLAlchemy",
        }
        for key, name in frameworks.items():
            if key in content.lower():
                if name not in profile.frameworks:
                    profile.frameworks.append(name)

def _detect_test_commands(path: Path, profile: ProjectProfile):
    """Detect test commands from project configuration."""
    # pytest
    if (path / "pytest.ini").exists() or (path / "pyproject.toml").exists():
        profile.test_commands.append("pytest")

    # tox
    if (path / "tox.ini").exists():
        profile.test_commands.append("tox")

    # npm test
    package_json = path / "package.json"
    if package_json.exists():
        try:
            content = json.loads(package_json.read_text())
            scripts = content.get("scripts", {})
            if "test" in scripts:
                profile.test_commands.append(f"npm test")
        except:
            pass

    # Default pytest if nothing found and Python project
    if profile.detected_type == ProjectType.PYTHON and not profile.test_commands:
        profile.test_commands.append("pytest")


# ==============================================================================
# Workspace Management
# ==============================================================================

class Workspace:
    """ASTA workspace management."""

    def __init__(self, path: Path):
        self.path = path
        self.projects_dir = path / ".asta" / "projects"
        self.global_dir = path / ".asta"

    def initialize(self) -> None:
        """Initialize workspace directories."""
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        (self.global_dir / "config").mkdir(parents=True, exist_ok=True)
        (self.global_dir / "cache").mkdir(parents=True, exist_ok=True)

    def get_project(self, project_id: str) -> Optional[Project]:
        """Get project by ID."""
        project_file = self.projects_dir / project_id / "project.json"
        if project_file.exists():
            data = json.loads(project_file.read_text())
            return Project.from_dict(data)
        return None

    def list_projects(self) -> List[Project]:
        """List all projects in workspace."""
        projects = []
        if self.projects_dir.exists():
            for project_dir in self.projects_dir.iterdir():
                project_file = project_dir / "project.json"
                if project_file.exists():
                    data = json.loads(project_file.read_text())
                    projects.append(Project.from_dict(data))
        return projects


# ==============================================================================
# Project Intake Validation
# ==============================================================================

def validate_project_intake(path: str) -> List[str]:
    """Validate project intake path. Returns list of errors (empty = valid)."""
    errors = []

    path_obj = Path(path)

    if not path_obj.exists():
        errors.append(f"Path does not exist: {path}")
        return errors

    if not path_obj.is_dir():
        errors.append(f"Path is not a directory: {path}")
        return errors

    # Check for read access
    try:
        list(path_obj.iterdir())
    except PermissionError:
        errors.append(f"No read permission for path: {path}")
        return errors

    # Check for write access to workspace (not source)
    workspace = Path.cwd() / ".asta"
    try:
        workspace.mkdir(parents=True, exist_ok=True)
        test_file = workspace / ".write_test"
        test_file.write_text("test")
        test_file.unlink()
    except PermissionError:
        errors.append(f"No write permission for workspace: {workspace}")
        return errors

    return errors


def confirm_project_ownership(path: str) -> bool:
    """Prompt user to confirm project ownership/authorization."""
    import click

    path_obj = Path(path).resolve()

    click.echo(f"Project intake: {path_obj}")
    click.echo(f"Detected project type: will be determined by inspection")
    click.echo("")
    click.echo("By proceeding, you confirm:")
    click.echo("  • You own or are authorized to test this project")
    click.echo("  • The project source will NOT be modified during testing")
    click.echo("  • Test execution will occur in isolated containers")
    click.echo("")

    return click.confirm("Do you confirm ownership/authorization?", default=True)


# ==============================================================================
# CLI Integration
# ==============================================================================

def project_add_command(path: str, scope_types: List[str] = None,
                        risk_approval: str = "high", workspace_path: Path = None) -> Project:
    """Project add CLI command implementation."""
    if workspace_path is None:
        workspace_path = Path.cwd()

    workspace = Workspace(workspace_path)
    workspace.initialize()

    # Validate intake
    errors = validate_project_intake(path)
    if errors:
        raise ValueError("Project intake validation failed:\n" + "\n".join(f"  • {e}" for e in errors))

    # Confirm ownership
    if not confirm_project_ownership(path):
        raise ValueError("Project ownership not confirmed. Aborting.")

    # Check if project already exists
    existing = Project.load(path, workspace_path)
    if existing:
        raise ValueError(f"Project already exists: {existing.id} ({existing.name})")

    # Create project
    project = Project.create(
        path=path,
        workspace_path=workspace_path,
        scope_types=scope_types,
        risk_approval=risk_approval
    )

    # Mark ownership confirmed
    project.ownership_confirmed = True
    project.save(workspace_path)

    return project


# ==============================================================================
# Run/Plan Management (simplified for M1a)
# ==============================================================================

@dataclass
class Plan:
    """Versioned testing plan with provenance."""
    project_name: str
    plan_revision: int
    content_hash: str
    generated_at: str
    scope_types: List[str]
    risk_approval: str
    checks: List[Dict] = field(default_factory=list)
    ai_off: bool = True

    def to_dict(self) -> Dict:
        return {
            "project_name": self.project_name,
            "plan_revision": self.plan_revision,
            "content_hash": self.content_hash,
            "generated_at": self.generated_at,
            "scope_types": self.scope_types,
            "risk_approval": self.risk_approval,
            "checks": self.checks,
            "ai_off": self.ai_off
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Plan':
        return cls(
            project_name=data["project_name"],
            plan_revision=data["plan_revision"],
            content_hash=data["content_hash"],
            generated_at=data["generated_at"],
            scope_types=data["scope_types"],
            risk_approval=data["risk_approval"],
            checks=data["checks"],
            ai_off=data.get("ai_off", True)
        )

    def save(self, workspace_path: Path, project_id: str) -> None:
        runs_dir = workspace_path / ".asta" / "projects" / project_id / "runs"
        runs_dir.mkdir(parents=True, exist_ok=True)

        plan_file = runs_dir / f"plan_{self.plan_revision}.json"
        plan_file.write_text(json.dumps(self.to_dict(), indent=2))


# ==============================================================================
# Project.get_runs (static method)
# ==============================================================================

def get_all_runs(workspace_path: Path) -> List[Dict]:
    """Get all runs across all projects."""
    runs = []
    projects_dir = workspace_path / ".asta" / "projects"
    if not projects_dir.exists():
        return runs

    for project_dir in projects_dir.iterdir():
        runs_dir = project_dir / "runs"
        if runs_dir.exists():
            for run_file in runs_dir.glob("run_*.json"):
                data = json.loads(run_file.read_text())
                runs.append(data)
    return runs

# Add to Project class
Project.get_runs = staticmethod(get_all_runs)


# ==============================================================================
# CLI Integration
# ==============================================================================

if __name__ == "__main__":
    import sys
    print("ASTA Models Module")
    print("Use: from asta.models import Project, ProjectProfile, Workspace")
    print("Project intake: project_add_command('/path/to/project')")