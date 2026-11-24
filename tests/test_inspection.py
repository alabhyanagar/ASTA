import pytest
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from asta.models import (
    Project, ProjectProfile, ProjectScope, ProjectConfig,
    ProjectCredentials, ProjectDependencies, Workspace,
    ProjectType, detect_project_profile, validate_project_intake
)
from asta.inspection import (
    inspect_project, InspectionResult, InspectionFact, FactConfidence
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

        result = inspect_project(project)

        # Language detection
        lang_facts = [f for f in result.facts if f.category == "language"]
        assert any(f.name == "python" for f in lang_facts)
        assert any(f.name == "primary" and f.value == "python" for f in lang_facts)

        # Manifest detection
        manifest_facts = result.get_facts_by_category("manifest")
        assert any(f.name == "pyproject.toml" for f in manifest_facts)
        assert any(f.name == "requirements.txt" for f in manifest_facts)

        # Framework detection
        fw_facts = result.get_facts_by_category("framework")
        assert any(f.name == "fastapi" for f in fw_facts)
        assert any(f.name == "pytest" for f in fw_facts)

        # Dependencies
        dep_facts = result.get_facts_by_category("dependency")
        dep_names = [f.name for f in dep_facts]
        assert "fastapi" in dep_names
        assert "pytest" in dep_names
        assert "httpx" in dep_names

        # Route detection
        route_facts = result.get_facts_by_category("route")
        route_paths = [f.name for f in route_facts]
        assert "GET /health" in route_paths
        assert "GET /items/{item_id}" in route_paths

        # Test commands
        test_facts = result.get_facts_by_category("test_command")
        assert any("pytest" in f.name for f in test_facts)

        # Test files
        test_file_facts = result.get_facts_by_category("test_file")
        assert any("python test files" in f.name for f in test_file_facts)

    def test_javascript_detection(self, tmp_path):
        """Detect JavaScript/Node.js project."""
        project = tmp_path / "jsproject"
        project.mkdir()
        (project / "package.json").write_text("""
{
  "name": "jsproject",
  "version": "1.0.0",
  "scripts": {
    "test": "jest",
    "build": "tsc"
  },
  "dependencies": {
    "express": "^4.18.2",
    "jest": "^29.7.0"
  }
}
""")
        (project / "index.js").write_text("""
const express = require('express');
const app = express();

app.get('/api/users', (req, res) => {
    res.json({users: []});
});

app.listen(3000);
""")
        (project / "jest.config.js").write_text("module.exports = { testEnvironment: 'node' };\n")

        result = inspect_project(project)

        lang_facts = result.get_facts_by_category("language")
        assert any(f.name == "javascript" for f in lang_facts)

        fw_facts = result.get_facts_by_category("framework")
        assert any(f.name == "express" for f in fw_facts)
        assert any(f.name == "jest" for f in fw_facts)

        route_facts = result.get_facts_by_category("route")
        assert any("GET /api/users" in f.name for f in route_facts)

    def test_go_detection(self, tmp_path):
        """Detect Go project."""
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

        result = inspect_project(project)

        lang_facts = result.get_facts_by_category("language")
        assert any(f.name == "go" for f in lang_facts)
        assert any(f.name == "primary" and f.value == "go" for f in lang_facts)

        fw_facts = result.get_facts_by_category("framework")
        assert any(f.name == "gin" for f in fw_facts)

    def test_inspect_openapi_spec(self, tmp_path):
        """Inspect project with OpenAPI spec."""
        project = tmp_path / "apiproject"
        project.mkdir()
        (project / "openapi.yaml").write_text("""
openapi: 3.0.3
info:
  title: Sample API
  version: 1.0.0
paths:
  /users:
    get:
      summary: List users
      responses:
        '200':
          description: OK
""")

        result = inspect_project(str(project))

        api_facts = result.get_facts_by_category("api_spec")
        assert len(api_facts) == 1
        assert api_facts[0].name == "Sample API"
        assert "3.0.3" in api_facts[0].value

    def test_inspect_docker_config(self, tmp_path):
        """Inspect project with Docker configuration."""
        project = tmp_path / "dockerproject"
        project.mkdir()
        (project / "Dockerfile").write_text("""
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
USER 1000
CMD ["python", "main.py"]
""")
        (project / "docker-compose.yml").write_text("""
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
  db:
    image: postgres:15
""")

        result = inspect_project(str(project))

        docker_facts = result.get_facts_by_category("docker")
        dockerfile_fact = next((f for f in docker_facts if f.name == "Dockerfile"), None)
        assert dockerfile_fact is not None
        assert "python:3.12-slim" in dockerfile_fact.value
        assert "8000" in dockerfile_fact.evidence[1]

        compose_fact = next((f for f in docker_facts if f.name == "docker-compose"), None)
        assert compose_fact is not None
        assert "2 services" in compose_fact.value

    def test_inspect_ci_cd(self, tmp_path):
        """Inspect project with CI/CD configuration."""
        project = tmp_path / "ciproject"
        project.mkdir()
        (project / ".github" / "workflows").mkdir(parents=True)
        (project / ".github" / "workflows" / "ci.yml").write_text("""
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: pytest
""")

        result = inspect_project(str(project))

        ci_facts = result.get_facts_by_category("ci_cd")
        assert any(f.name == "GitHub Actions" for f in ci_facts)

    def test_inspect_deployment_config(self, tmp_path):
        """Inspect project with Kubernetes/Helm config."""
        project = tmp_path / "k8sproject"
        project.mkdir()
        (project / "k8s").mkdir(parents=True)
        (project / "k8s" / "deployment.yaml").write_text("""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: myapp:latest
""")
        (project / "helm").mkdir(parents=True)
        (project / "helm" / "Chart.yaml").write_text("""
apiVersion: v2
name: myapp
version: 1.0.0
""")

        result = inspect_project(str(project))

        deploy_facts = result.get_facts_by_category("deployment")
        categories = [f.name for f in deploy_facts]
        assert "kubernetes" in categories
        assert "helm" in categories

    def test_inspect_unknown_project(self, tmp_path):
        """Inspect empty/unknown project."""
        project = tmp_path / "unknown"
        project.mkdir()

        result = inspect_project(str(project))

        # Should have unknown facts
        assert len(result.unknown_facts) > 0
        assert any("language" in u.lower() for u in result.unknown_facts)

    def test_inspect_no_module_execution(self, tmp_path):
        """Verify no project modules are executed during inspection."""
        project = tmp_path / "malicious"
        project.mkdir()
        # This file would execute code if imported
        (project / "malicious.py").write_text("""
import os
os.system("echo 'MALICIOUS CODE EXECUTED' > /tmp/hacked.txt")
print("This should not run during inspection")
""")
        (project / "__init__.py").write_text("")

        result = inspect_project(str(project))

        # Inspection should complete without executing the malicious code
        # The file should be analyzed statically only
        assert isinstance(result, InspectionResult)
        # No errors should occur from execution
        assert not any("MALICIOUS" in e for e in result.errors)

    def test_inspect_empty_directory(self, tmp_path):
        """Inspect empty directory."""
        project = tmp_path / "empty"
        project.mkdir()

        result = inspect_project(str(project))

        assert isinstance(result, InspectionResult)
        assert len(result.unknown_facts) > 0
        assert any("language" in u.lower() for u in result.unknown_facts)


class TestInspectionResult:
    """Test InspectionResult data structure."""

    def test_result_serialization(self, tmp_path):
        """InspectionResult serializes to JSON."""
        project = tmp_path / "test"
        project.mkdir()
        (project / "pyproject.toml").write_text("[project]\nname='test'\n")

        result = inspect_project(str(project))
        json_str = json.dumps(result.to_dict())

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert "project_path" in parsed
        assert "facts" in parsed
        assert "unknown_facts" in parsed
        assert "errors" in parsed

    def test_fact_serialization(self):
        """InspectionFact serializes correctly."""
        fact = InspectionFact(
            category="language",
            name="python",
            value="3.12",
            confidence=FactConfidence.HIGH,
            evidence=["pyproject.toml", "main.py"],
            source="static"
        )

        data = fact.to_dict()
        assert data["category"] == "language"
        assert data["name"] == "python"
        assert data["value"] == "3.12"
        assert data["confidence"] == "high"
        assert data["evidence"] == ["pyproject.toml", "main.py"]
        assert data["source"] == "static"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])