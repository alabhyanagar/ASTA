#!/usr/bin/env python3
"""
ASTA M1 Models Tests
"""

import pytest
import json
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from asta.models import (
    Project, ProjectProfile, ProjectScope, ProjectConfig,
    ProjectCredentials, ProjectDependencies, Workspace,
    ProjectType, detect_project_profile, validate_project_intake
)


class TestProjectProfile:
    """Test project profile detection."""

    def test_python_detection_pyproject(self, tmp_path):
        """Detect Python project from pyproject.toml."""
        project = tmp_path / "myproject"
        project.mkdir()
        (project / "pyproject.toml").write_text("""
[project]
name = "myproject"
version = "1.0.0"
dependencies = ["fastapi", "pytest", "httpx"]

[tool.pytest.ini_options]
testpaths = ["tests"]
""")
        (project / "main.py").write_text("""
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}
""")
        (project / "requirements.txt").write_text("fastapi==0.104.1\npytest==8.2.0\nhttpx==0.27.0\n")
        (project / "tests").mkdir(parents=True, exist_ok=True)
        (project / "tests" / "test_main.py").write_text("def test_health():\n    pass\n")

        profile = detect_project_profile(project)

        assert profile.detected_type == ProjectType.PYTHON
        assert profile.language == "python"
        assert profile.confidence > 0.5
        assert "pyproject.toml" in profile.manifests

    def test_python_detection_setup_py(self, tmp_path):
        """Detect Python project from setup.py."""
        project = tmp_path / "myproject"
        project.mkdir()
        (project / "setup.py").write_text("from setuptools import setup\nsetup(name='test')\n")

        profile = detect_project_profile(project)

        assert profile.detected_type == ProjectType.PYTHON
        assert "setup.py" in profile.manifests

    def test_javascript_detection(self, tmp_path):
        """Detect JavaScript project from package.json."""
        project = tmp_path / "jsproject"
        project.mkdir()
        (project / "package.json").write_text('{"name": "jsproject", "version": "1.0.0"}\n')

        profile = detect_project_profile(project)

        assert profile.detected_type == ProjectType.JAVASCRIPT
        assert profile.language == "javascript"
        assert "package.json" in profile.manifests

    def test_typescript_detection(self, tmp_path):
        """Detect TypeScript project from tsconfig.json."""
        project = tmp_path / "tsproject"
        project.mkdir()
        (project / "package.json").write_text('{"name": "test"}\n')
        (project / "tsconfig.json").write_text('{"compilerOptions": {}}\n')

        profile = detect_project_profile(project)

        assert profile.detected_type == ProjectType.TYPESCRIPT
        assert profile.language == "typescript"
        assert "tsconfig.json" in profile.manifests

    def test_go_detection(self, tmp_path):
        """Detect Go project from go.mod."""
        project = tmp_path / "goproject"
        project.mkdir()
        (project / "go.mod").write_text("module example.com/myproject\n\ngo 1.21\n\nrequire github.com/gin-gonic/gin v1.9.1\n")
        (project / "main.go").write_text("""
package main

import "github.com/gin-gonic/gin"

func main() {
    r := gin.Default()
    r.GET("/ping", func(c *gin.Context) {
        c.JSON(200, gin.H{"message": "pong"})
    })
    r.Run()
}
""")

        profile = detect_project_profile(project)

        assert profile.detected_type == ProjectType.GO
        assert profile.language == "go"
        assert "go.mod" in profile.manifests

    def test_fastapi_detection(self, tmp_path):
        """Detect FastAPI framework from pyproject.toml."""
        project = tmp_path / "fastapiproject"
        project.mkdir()
        (project / "pyproject.toml").write_text("""
[project]
name = "fastapiproject"
version = "1.0.0"
dependencies = ["fastapi", "uvicorn"]
""")
        (project / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n")

        profile = detect_project_profile(project)

        assert "FastAPI" in profile.frameworks

    def test_pytest_detection(self, tmp_path):
        """Detect pytest test command."""
        project = tmp_path / "pytestproject"
        project.mkdir()
        (project / "pyproject.toml").write_text("[tool.pytest.ini_options]\ntestpaths = ['tests']\n")

        profile = detect_project_profile(project)

        assert "pytest" in profile.test_commands

    def test_unknown_project(self, tmp_path):
        """Unknown project type for empty directory."""
        project = tmp_path / "unknown"
        project.mkdir()

        profile = detect_project_profile(project)

        assert profile.detected_type == ProjectType.UNKNOWN
        assert profile.confidence == 0.0
        assert len(profile.unknown) > 0


class TestProjectModel:
    """Test Project model."""

    def test_project_creation(self, tmp_path):
        """Create project from path."""
        project_path = tmp_path / "test-project"
        project_path.mkdir()
        (project_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")

        workspace = tmp_path / "workspace"
        workspace.mkdir()

        project = Project.create(
            path=str(project_path),
            workspace_path=workspace,
            scope_types=["unit", "integration"],
            risk_approval="high"
        )

        assert project.id.startswith("proj_")
        assert project.name == "test-project"
        assert project.source_path == str(project_path.resolve())
        assert project.profile.detected_type == ProjectType.PYTHON
        assert project.scope.types == ["unit", "integration"]
        assert project.scope.risk_approval == "high"
        assert project.ownership_confirmed == False

    def test_project_save_load(self, tmp_path):
        """Project saves and loads correctly."""
        project_path = tmp_path / "test-project"
        project_path.mkdir()
        (project_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")

        workspace = tmp_path / "workspace"
        workspace.mkdir()

        # Create and save
        project = Project.create(
            path=str(project_path),
            workspace_path=workspace,
            scope_types=["unit"]
        )

        # Load
        loaded = Project.load(str(project_path), workspace)

        assert loaded is not None
        assert loaded.id == project.id
        assert loaded.name == project.name
        assert loaded.source_path == project.source_path
        assert loaded.profile.detected_type == project.profile.detected_type

    def test_project_duplicate_prevention(self, tmp_path):
        """Creating same project twice raises error."""
        project_path = tmp_path / "test-project"
        project_path.mkdir()
        (project_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")

        workspace = tmp_path / "workspace"
        workspace.mkdir()

        Project.create(path=str(project_path), workspace_path=workspace)

        # Second creation should fail
        with pytest.raises(ValueError, match="already exists"):
            Project.create(path=str(project_path), workspace_path=workspace)

    def test_project_serialization(self, tmp_path):
        """Project serializes to/from dict correctly."""
        project_path = tmp_path / "test-project"
        project_path.mkdir()
        (project_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")

        workspace = tmp_path / "workspace"
        workspace.mkdir()

        project = Project.create(
            path=str(project_path),
            workspace_path=workspace,
            scope_types=["unit", "api"],
            risk_approval="critical"
        )

        data = project.to_dict()

        # Check all fields present
        assert "id" in data
        assert "name" in data
        assert "source_path" in data
        assert "profile" in data
        assert "scope" in data
        assert data["scope"]["types"] == ["unit", "api"]
        assert data["scope"]["risk_approval"] == "critical"
        assert "config" in data
        assert "credentials" in data
        assert "dependencies" in data

        # Round-trip
        loaded = Project.from_dict(data)
        assert loaded.id == project.id
        assert loaded.scope.types == ["unit", "api"]
        assert loaded.scope.risk_approval == "critical"


class TestWorkspace:
    """Test Workspace management."""

    def test_workspace_initialize(self, tmp_path):
        """Workspace initializes directories."""
        workspace = Workspace(tmp_path)
        workspace.initialize()

        assert (tmp_path / ".asta" / "projects").exists()
        assert (tmp_path / ".asta" / "config").exists()
        assert (tmp_path / ".asta" / "cache").exists()

    def test_workspace_list_projects(self, tmp_path):
        """Workspace lists projects."""
        workspace = Workspace(tmp_path)
        workspace.initialize()

        # Create a project
        project_path = tmp_path / "proj1"
        project_path.mkdir()
        (project_path / "pyproject.toml").write_text("[project]\nname='test'\n")

        Project.create(str(project_path), tmp_path)

        projects = workspace.list_projects()
        assert len(projects) == 1
        assert projects[0].name == "proj1"

    def test_workspace_get_project(self, tmp_path):
        """Workspace gets project by ID."""
        workspace = Workspace(tmp_path)
        workspace.initialize()

        project_path = tmp_path / "proj1"
        project_path.mkdir()
        (project_path / "pyproject.toml").write_text("[project]\nname='test'\n")

        project = Project.create(str(project_path), tmp_path)

        loaded = workspace.get_project(project.id)
        assert loaded is not None
        assert loaded.id == project.id


class TestProjectIntakeValidation:
    """Test project intake validation."""

    def test_valid_path(self, tmp_path):
        """Valid directory passes validation."""
        project_path = tmp_path / "project"
        project_path.mkdir()

        errors = validate_project_intake(str(project_path))
        assert len(errors) == 0

    def test_nonexistent_path(self):
        """Nonexistent path fails validation."""
        errors = validate_project_intake("/nonexistent/path")
        assert len(errors) > 0
        assert "does not exist" in errors[0]

    def test_file_not_directory(self, tmp_path):
        """File path fails validation."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("test")

        errors = validate_project_intake(str(file_path))
        assert len(errors) > 0
        assert "not a directory" in errors[0]

    def test_permission_error(self, tmp_path):
        """Permission error handled."""
        # This test is platform-dependent; skip on Windows
        import os
        if os.name == 'nt':
            pytest.skip("Permission test not applicable on Windows")

        project_path = tmp_path / "project"
        project_path.mkdir()
        project_path.chmod(0o000)  # No permissions

        try:
            errors = validate_project_intake(str(project_path))
            assert len(errors) > 0
            assert "permission" in errors[0].lower()
        finally:
            project_path.chmod(0o755)  # Restore for cleanup


class TestProjectProfileSerialization:
    """Test ProjectProfile serialization."""

    def test_profile_to_from_dict(self):
        """Profile round-trips through dict."""
        profile = ProjectProfile(
            detected_type=ProjectType.PYTHON,
            language="python",
            version="3.12",
            frameworks=["FastAPI", "pytest"],
            manifests=["pyproject.toml"],
            build_commands=["pip install -e ."],
            test_commands=["pytest"],
            dependencies=["fastapi", "pytest"],
            confidence=0.9,
            unknown=["version not found"]
        )

        data = profile.to_dict()
        loaded = ProjectProfile.from_dict(data)

        assert loaded.detected_type == ProjectType.PYTHON
        assert loaded.language == "python"
        assert loaded.version == "3.12"
        assert loaded.frameworks == ["FastAPI", "pytest"]
        assert loaded.confidence == 0.9
        assert loaded.unknown == ["version not found"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])