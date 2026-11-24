#!/usr/bin/env python3
"""
ASTA M1 Static Project Inspection Engine

Performs safe static analysis of projects without executing/importing modules.
Every fact has evidence; unknown remains unknown.
Deterministic rules only; no AI inference in M1.
"""

import json
import re
import ast
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from enum import Enum

# ==============================================================================
# Inspection Result Models
# ==============================================================================

class FactConfidence(str, Enum):
    HIGH = "high"      # Direct evidence from files
    MEDIUM = "medium"  # Inferred from patterns
    LOW = "low"        # Heuristic match
    UNKNOWN = "unknown"  # Cannot determine

@dataclass
class InspectionFact:
    """A single fact discovered during inspection."""
    category: str  # language, framework, manifest, build, test, dependency, route, api, deployment
    name: str      # e.g., "fastapi", "pytest", "Dockerfile"
    value: Optional[str] = None  # e.g., version, path
    confidence: FactConfidence = FactConfidence.UNKNOWN
    evidence: List[str] = field(default_factory=list)  # File paths, line numbers, patterns
    source: str = "static"  # static, heuristic, unknown

    def to_dict(self) -> Dict:
        return {
            "category": self.category,
            "name": self.name,
            "value": self.value,
            "confidence": self.confidence.value,
            "evidence": self.evidence,
            "source": self.source
        }

@dataclass
class InspectionResult:
    """Complete inspection result for a project."""
    project_path: str
    facts: List[InspectionFact] = field(default_factory=list)
    unknown_facts: List[str] = field(default_factory=list)  # Things we couldn't determine
    errors: List[str] = field(default_factory=list)  # Inspection errors (not failures)

    def get_facts_by_category(self, category: str) -> List[InspectionFact]:
        return [f for f in self.facts if f.category == category]

    def get_high_confidence_facts(self) -> List[InspectionFact]:
        return [f for f in self.facts if f.confidence in [FactConfidence.HIGH, FactConfidence.MEDIUM]]

    def to_dict(self) -> Dict:
        return {
            "project_path": self.project_path,
            "facts": [f.to_dict() for f in self.facts],
            "unknown_facts": self.unknown_facts,
            "errors": self.errors
        }

# ==============================================================================
# Static Analysis Engine
# ==============================================================================

class StaticInspector:
    """Main static inspection engine - no module execution."""

    def __init__(self, project_path: Path):
        self.project_path = project_path.resolve()
        self.result = InspectionResult(project_path=str(self.project_path))
        self._visited_files: Set[Path] = set()

    def inspect(self) -> InspectionResult:
        """Run complete static inspection."""
        # Run all detection modules
        self._detect_language()
        self._detect_manifests()
        self._detect_frameworks()
        self._detect_dependencies()
        self._detect_build_commands()
        self._detect_test_commands()
        self._detect_routes()
        self._detect_api_specs()
        self._detect_deployment_config()
        self._detect_docker_config()
        self._detect_ci_cd_config()
        self._detect_test_files()

        # Summarize unknowns
        self._summarize_unknowns()

        return self.result

    # ==========================================================================
    # Language Detection
    # ==========================================================================

    def _detect_language(self):
        """Detect primary programming language(s)."""
        language_indicators = {
            "python": {
                "files": ["*.py", "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "Pipfile", "poetry.lock"],
                "patterns": ["import ", "from ", "def ", "class "]
            },
            "javascript": {
                "files": ["*.js", "*.jsx", "package.json", "yarn.lock", "pnpm-lock.yaml"],
                "patterns": ["import ", "export ", "const ", "function "]
            },
            "typescript": {
                "files": ["*.ts", "*.tsx", "tsconfig.json"],
                "patterns": ["interface ", "type ", ": string", ": number"]
            },
            "go": {
                "files": ["*.go", "go.mod", "go.sum"],
                "patterns": ["package ", "func ", "import "]
            },
            "java": {
                "files": ["*.java", "pom.xml", "build.gradle", "build.gradle.kts"],
                "patterns": ["public class", "import ", "package "]
            },
            "rust": {
                "files": ["*.rs", "Cargo.toml", "Cargo.lock"],
                "patterns": ["fn ", "struct ", "impl ", "use "]
            },
            "csharp": {
                "files": ["*.cs", "*.csproj", "*.sln"],
                "patterns": ["namespace ", "class ", "using "]
            },
            "ruby": {
                "files": ["*.rb", "Gemfile", "Gemfile.lock", "Rakefile"],
                "patterns": ["def ", "class ", "module ", "require "]
            },
            "php": {
                "files": ["*.php", "composer.json", "composer.lock"],
                "patterns": ["<?php", "namespace ", "class ", "function "]
            }
        }

        detected_languages = {}

        for lang, config in language_indicators.items():
            evidence = []
            score = 0

            # Check for indicator files
            for pattern in config["files"]:
                matches = list(self.project_path.rglob(pattern))
                if matches:
                    evidence.extend([str(p.relative_to(self.project_path)) for p in matches[:5]])
                    score += 10

            # Check for language patterns in source files (limited sampling)
            if score > 0:
                source_files = list(self.project_path.rglob("*.py"))[:10]  # Sample
                for sf in source_files:
                    try:
                        content = sf.read_text(encoding="utf-8", errors="ignore")
                        for pat in config["patterns"]:
                            if pat in content:
                                evidence.append(f"{sf.relative_to(self.project_path)}: contains '{pat}'")
                                score += 1
                                break
                    except:
                        pass

            if score > 0:
                confidence = FactConfidence.HIGH if score >= 20 else FactConfidence.MEDIUM if score >= 10 else FactConfidence.LOW
                self.result.facts.append(InspectionFact(
                    category="language",
                    name=lang,
                    confidence=confidence,
                    evidence=evidence[:10],  # Limit evidence
                    source="static"
                ))
                detected_languages[lang] = score

        # Mark primary language
        if detected_languages:
            primary = max(detected_languages, key=detected_languages.get)
            self.result.facts.append(InspectionFact(
                category="language",
                name="primary",
                value=primary,
                confidence=FactConfidence.HIGH,
                evidence=[f"Primary language detected: {primary}"],
                source="static"
            ))
        else:
            self.result.unknown_facts.append("Primary programming language could not be determined")

    # ==========================================================================
    # Manifest Detection
    # ==========================================================================

    def _detect_manifests(self):
        """Detect project manifest/build files."""
        manifest_patterns = {
            "python": {
                "pyproject.toml": "Python project metadata (PEP 621)",
                "setup.py": "Python setuptools setup script",
                "setup.cfg": "Python setuptools configuration",
                "requirements.txt": "Python pip requirements",
                "Pipfile": "Python Pipenv dependencies",
                "Pipfile.lock": "Python Pipenv locked dependencies",
                "poetry.lock": "Python Poetry locked dependencies",
                "requirements-dev.txt": "Python dev requirements",
                "requirements-test.txt": "Python test requirements"
            },
            "javascript": {
                "package.json": "Node.js package manifest",
                "package-lock.json": "npm lock file",
                "yarn.lock": "Yarn lock file",
                "pnpm-lock.yaml": "pnpm lock file",
                "bower.json": "Bower manifest (deprecated)"
            },
            "go": {
                "go.mod": "Go module definition",
                "go.sum": "Go module checksums"
            },
            "java": {
                "pom.xml": "Maven project descriptor",
                "build.gradle": "Gradle build script (Groovy)",
                "build.gradle.kts": "Gradle build script (Kotlin)",
                "settings.gradle": "Gradle settings",
                "settings.gradle.kts": "Gradle settings (Kotlin)"
            },
            "rust": {
                "Cargo.toml": "Cargo package manifest",
                "Cargo.lock": "Cargo lock file"
            },
            "csharp": {
                "*.csproj": "C# project file",
                "*.sln": "Visual Studio solution"
            },
            "ruby": {
                "Gemfile": "Ruby Bundler dependencies",
                "Gemfile.lock": "Bundler locked dependencies"
            },
            "php": {
                "composer.json": "Composer package manifest",
                "composer.lock": "Composer lock file"
            },
            "docker": {
                "Dockerfile": "Docker container definition",
                "docker-compose.yml": "Docker Compose configuration",
                "docker-compose.yaml": "Docker Compose configuration",
                ".dockerignore": "Docker ignore file"
            },
            "kubernetes": {
                "k8s/*.yaml": "Kubernetes manifests",
                "k8s/*.yml": "Kubernetes manifests",
                "helm/Chart.yaml": "Helm chart",
                "helm/values.yaml": "Helm values"
            },
            "terraform": {
                "*.tf": "Terraform configuration",
                "*.tfvars": "Terraform variables"
            }
        }

        for category, patterns in manifest_patterns.items():
            for pattern, description in patterns.items():
                if "*" in pattern:
                    matches = list(self.project_path.rglob(pattern))
                else:
                    matches = [self.project_path / pattern] if (self.project_path / pattern).exists() else []

                for match in matches:
                    try:
                        rel_path = match.relative_to(self.project_path)
                        self.result.facts.append(InspectionFact(
                            category="manifest",
                            name=pattern,
                            value=str(rel_path),
                            confidence=FactConfidence.HIGH,
                            evidence=[f"Found {pattern}: {description}"],
                            source="static"
                        ))
                    except:
                        pass

    # ==========================================================================
    # Framework Detection
    # ==========================================================================

    def _detect_frameworks(self):
        """Detect web/application frameworks from configuration files."""
        framework_patterns = {
            "python": {
                "fastapi": ["fastapi", "FastAPI"],
                "django": ["django", "Django"],
                "flask": ["flask", "Flask"],
                "starlette": ["starlette", "Starlette"],
                "tornado": ["tornado"],
                "aiohttp": ["aiohttp"],
                "sanic": ["sanic"],
                "bottle": ["bottle"],
                "pyramid": ["pyramid"],
                "cherrypy": ["cherrypy"],
                "falcon": ["falcon"],
                "quart": ["quart"],
                "pydantic": ["pydantic"],
                "sqlalchemy": ["sqlalchemy"],
                "alembic": ["alembic"],
                "celery": ["celery"],
                "pytest": ["pytest"],
                "httpx": ["httpx"],
                "requests": ["requests"],
                "uvicorn": ["uvicorn"],
                "gunicorn": ["gunicorn"]
            },
            "javascript": {
                "express": ["express"],
                "koa": ["koa"],
                "fastify": ["fastify"],
                "nest": ["@nestjs/core", "@nestjs/common"],
                "next": ["next"],
                "nuxt": ["nuxt"],
                "react": ["react"],
                "vue": ["vue"],
                "svelte": ["svelte"],
                "angular": ["@angular/core"],
                "jest": ["jest"],
                "mocha": ["mocha"],
                "vitest": ["vitest"],
                "playwright": ["playwright"],
                "cypress": ["cypress"],
                "webpack": ["webpack"],
                "vite": ["vite"],
                "esbuild": ["esbuild"]
            },
            "go": {
                "gin": ["github.com/gin-gonic/gin"],
                "echo": ["github.com/labstack/echo"],
                "fiber": ["github.com/gofiber/fiber"],
                "chi": ["github.com/go-chi/chi"],
                "gorilla/mux": ["github.com/gorilla/mux"],
                "gorm": ["gorm.io/gorm"],
                "sqlx": ["github.com/jmoiron/sqlx"],
                "testify": ["github.com/stretchr/testify"]
            }
        }

        for lang, frameworks in framework_patterns.items():
            # Check manifest files for framework dependencies
            manifest_files = ["pyproject.toml", "setup.py", "requirements.txt", "Pipfile",
                            "package.json", "go.mod", "Cargo.toml", "pom.xml", "build.gradle"]

            for manifest in manifest_files:
                manifest_path = self.project_path / manifest
                if manifest_path.exists():
                    try:
                        content = manifest_path.read_text(encoding="utf-8", errors="ignore").lower()
                        for fw_name, patterns in frameworks.items():
                            for pattern in patterns:
                                if pattern.lower() in content:
                                    self.result.facts.append(InspectionFact(
                                        category="framework",
                                        name=fw_name,
                                        confidence=FactConfidence.HIGH,
                                        evidence=[f"Found in {manifest}: {pattern}"],
                                        source="static"
                                    ))
                                    # Also add as tool config for pytest
                                    if fw_name == "pytest" and manifest in ["pyproject.toml", "setup.cfg", "pytest.ini"]:
                                        self.result.facts.append(InspectionFact(
                                            category="tool",
                                            name="pytest",
                                            confidence=FactConfidence.HIGH,
                                            evidence=[f"Found pytest config in {manifest}"],
                                            source="static"
                                        ))
                                    break  # One match per framework per manifest
                    except:
                        pass

    # ==========================================================================
    # Dependency Detection
    # ==========================================================================

    def _detect_dependencies(self):
        """Detect project dependencies from lock files and manifests."""
        dep_files = {
            "requirements.txt": self._parse_requirements_txt,
            "requirements-dev.txt": self._parse_requirements_txt,
            "requirements-test.txt": self._parse_requirements_txt,
            "Pipfile.lock": self._parse_pipfile_lock,
            "poetry.lock": self._parse_poetry_lock,
            "package-lock.json": self._parse_package_lock,
            "yarn.lock": self._parse_yarn_lock,
            "go.sum": self._parse_go_sum,
            "Cargo.lock": self._parse_cargo_lock,
            "composer.lock": self._parse_composer_lock
        }

        for filename, parser in dep_files.items():
            path = self.project_path / filename
            if path.exists():
                try:
                    deps = parser(path)
                    for dep in deps:
                        self.result.facts.append(InspectionFact(
                            category="dependency",
                            name=dep["name"],
                            value=dep.get("version"),
                            confidence=FactConfidence.HIGH,
                            evidence=[f"Found in {filename}: {dep['name']}=={dep.get('version', 'unknown')}"],
                            source="static"
                        ))
                except Exception as e:
                    self.result.errors.append(f"Failed to parse {filename}: {e}")

    def _parse_requirements_txt(self, path: Path) -> List[Dict]:
        """Parse requirements.txt format."""
        deps = []
        content = path.read_text(encoding="utf-8", errors="ignore")
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("-"):
                parts = re.split(r'[=<>!~]', line)
                name = parts[0].strip()
                version = line[len(name):].strip() if len(line) > len(name) else None
                deps.append({"name": name, "version": version})
        return deps

    def _parse_pipfile_lock(self, path: Path) -> List[Dict]:
        import json
        data = json.loads(path.read_text())
        deps = []
        for section in ["default", "develop"]:
            for name, info in data.get(section, {}).items():
                deps.append({"name": name, "version": info.get("version", "").lstrip("==")})
        return deps

    def _parse_poetry_lock(self, path: Path) -> List[Dict]:
        import toml
        data = toml.loads(path.read_text())
        deps = []
        for pkg in data.get("package", []):
            deps.append({"name": pkg["name"], "version": pkg["version"]})
        return deps

    def _parse_package_lock(self, path: Path) -> List[Dict]:
        import json
        data = json.loads(path.read_text())
        deps = []
        for name, info in data.get("dependencies", {}).items():
            deps.append({"name": name, "version": info.get("version")})
        return deps

    def _parse_yarn_lock(self, path: Path) -> List[Dict]:
        deps = []
        content = path.read_text()
        for line in content.splitlines():
            if line.startswith('"') and '@' in line:
                parts = line.split('@')
                name = parts[0].strip('"')
                version = parts[1].split()[0] if len(parts) > 1 else None
                deps.append({"name": name, "version": version})
        return deps

    def _parse_go_sum(self, path: Path) -> List[Dict]:
        deps = []
        content = path.read_text()
        for line in content.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                deps.append({"name": parts[0], "version": parts[1]})
        return deps

    def _parse_cargo_lock(self, path: Path) -> List[Dict]:
        import toml
        data = toml.loads(path.read_text())
        deps = []
        for pkg in data.get("package", []):
            deps.append({"name": pkg["name"], "version": pkg["version"]})
        return deps

    def _parse_composer_lock(self, path: Path) -> List[Dict]:
        import json
        data = json.loads(path.read_text())
        deps = []
        for pkg in data.get("packages", []):
            deps.append({"name": pkg["name"], "version": pkg["version"]})
        return deps

    # ==========================================================================
    # Build/Test Command Detection
    # ==========================================================================

    def _detect_build_commands(self):
        """Detect build commands from project configuration."""
        build_patterns = {
            "python": {
                "files": ["pyproject.toml", "setup.py", "setup.cfg", "Makefile", "makefile"],
                "commands": ["pip install -e .", "python setup.py build", "pip wheel .", "poetry build", "pipx build"]
            },
            "javascript": {
                "files": ["package.json", "Makefile", "makefile"],
                "commands": ["npm run build", "yarn build", "pnpm build", "npm run compile"]
            },
            "go": {
                "files": ["go.mod", "Makefile", "makefile"],
                "commands": ["go build", "go build ./..."]
            },
            "rust": {
                "files": ["Cargo.toml", "Makefile", "makefile"],
                "commands": ["cargo build", "cargo build --release"]
            },
            "java": {
                "files": ["pom.xml", "build.gradle", "build.gradle.kts"],
                "commands": ["mvn compile", "mvn package", "./gradlew build", "./gradlew assemble"]
            },
            "docker": {
                "files": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"],
                "commands": ["docker build .", "docker-compose build"]
            }
        }

        for lang, config in build_patterns.items():
            for pattern_file in config["files"]:
                if pattern_file in ["Makefile", "makefile"]:
                    matches = list(self.project_path.glob(pattern_file))
                else:
                    matches = [self.project_path / pattern_file] if (self.project_path / pattern_file).exists() else []

                if matches:
                    for cmd in config["commands"]:
                        self.result.facts.append(InspectionFact(
                            category="build_command",
                            name=cmd,
                            confidence=FactConfidence.MEDIUM,
                            evidence=[f"Inferred from {matches[0].name}"],
                            source="heuristic"
                        ))

    def _detect_test_commands(self):
        """Detect test commands from project configuration."""
        test_patterns = {
            "python": {
                "files": ["pytest.ini", "pyproject.toml", "setup.cfg", "tox.ini", "Makefile", "makefile"],
                "commands": ["pytest", "pytest -v", "pytest --cov", "tox", "python -m pytest"]
            },
            "javascript": {
                "files": ["package.json", "jest.config.js", "jest.config.ts", "vitest.config.ts", "Makefile"],
                "commands": ["npm test", "yarn test", "pnpm test", "jest", "vitest", "mocha"]
            },
            "go": {
                "files": ["go.mod", "Makefile", "makefile"],
                "commands": ["go test ./...", "go test -v ./...", "go test -race ./..."]
            },
            "rust": {
                "files": ["Cargo.toml", "Makefile", "makefile"],
                "commands": ["cargo test", "cargo test --all"]
            },
            "java": {
                "files": ["pom.xml", "build.gradle", "build.gradle.kts"],
                "commands": ["mvn test", "./gradlew test"]
            }
        }

        for lang, config in test_patterns.items():
            for pattern_file in config["files"]:
                if pattern_file in ["Makefile", "makefile"]:
                    matches = list(self.project_path.glob(pattern_file))
                else:
                    matches = [self.project_path / pattern_file] if (self.project_path / pattern_file).exists() else []

                if matches:
                    for cmd in config["commands"]:
                        self.result.facts.append(InspectionFact(
                            category="test_command",
                            name=cmd,
                            confidence=FactConfidence.MEDIUM,
                            evidence=[f"Inferred from {matches[0].name}"],
                            source="heuristic"
                        ))

    # ==========================================================================
    # Route/API Spec Detection
    # ==========================================================================

    def _detect_routes(self):
        """Detect API routes from source code (static analysis only)."""
        # Look for route definitions in Python files
        python_files = list(self.project_path.rglob("*.py"))[:50]  # Limit sampling
        js_files = list(self.project_path.rglob("*.js"))[:50] + list(self.project_path.rglob("*.ts"))[:50]

        route_patterns = [
            (r'@app\.(get|post|put|delete|patch|head|options)\s*\(\s*["\']([^"\']+)', "fastapi/flask"),
            (r'@router\.(get|post|put|delete|patch|head|options)\s*\(\s*["\']([^"\']+)', "fastapi"),
            (r'app\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)', "express-like"),
            (r'router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)', "express"),
            (r'Route\s*\(\s*["\']([^"\']+)', "generic"),
        ]

        # Check Python files
        for py_file in python_files:
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                for pattern, framework in route_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        if isinstance(match, tuple):
                            method, path = match[0], match[1]
                        else:
                            method = "GET"
                            path = match
                        self.result.facts.append(InspectionFact(
                            category="route",
                            name=f"{method.upper()} {path}",
                            value=framework,
                            confidence=FactConfidence.MEDIUM,
                            evidence=[f"Found in {py_file.relative_to(self.project_path)}"],
                            source="static"
                        ))
            except:
                pass

        # Check JavaScript/TypeScript files for Express-style routes
        js_route_patterns = [
            (r'app\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)', "express"),
            (r'router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)', "express"),
        ]

        for js_file in js_files:
            try:
                content = js_file.read_text(encoding="utf-8", errors="ignore")
                for pattern, framework in js_route_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        if isinstance(match, tuple):
                            method, path = match[0], match[1]
                        else:
                            method = "GET"
                            path = match
                        self.result.facts.append(InspectionFact(
                            category="route",
                            name=f"{method.upper()} {path}",
                            value=framework,
                            confidence=FactConfidence.MEDIUM,
                            evidence=[f"Found in {js_file.relative_to(self.project_path)}"],
                            source="static"
                        ))
            except:
                pass

    def _detect_api_specs(self):
        """Detect OpenAPI/Swagger specifications."""
        spec_files = [
            "openapi.json", "openapi.yaml", "openapi.yml",
            "swagger.json", "swagger.yaml", "swagger.yml",
            "api.json", "api.yaml", "api.yml",
            "spec.json", "spec.yaml", "spec.yml"
        ]

        for spec_file in spec_files:
            path = self.project_path / spec_file
            if path.exists():
                try:
                    if path.suffix == ".json":
                        spec = json.loads(path.read_text())
                    else:
                        import yaml
                        spec = yaml.safe_load(path.read_text())

                    openapi_version = spec.get("openapi") or spec.get("swagger")
                    title = spec.get("info", {}).get("title", "Unknown API")
                    version = spec.get("info", {}).get("version", "unknown")

                    self.result.facts.append(InspectionFact(
                        category="api_spec",
                        name=title,
                        value=f"OpenAPI {openapi_version or 'unknown'}",
                        confidence=FactConfidence.HIGH,
                        evidence=[f"Found {spec_file}: {title} v{version}"],
                        source="static"
                    ))
                except Exception as e:
                    self.result.errors.append(f"Failed to parse {spec_file}: {e}")

    # ==========================================================================
    # Deployment Configuration
    # ==========================================================================

    def _detect_deployment_config(self):
        """Detect deployment configuration files."""
        deploy_patterns = {
            "kubernetes": ["k8s/*.yaml", "k8s/*.yml", "manifests/*.yaml", "manifests/*.yml",
                          "deploy/*.yaml", "deploy/*.yml", "helm/Chart.yaml"],
            "docker": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml", ".dockerignore"],
            "terraform": ["*.tf", "*.tfvars"],
            "ansible": ["playbook.yml", "playbook.yaml", "site.yml", "site.yaml", "roles/"],
            "helm": ["helm/Chart.yaml", "helm/values.yaml", "helm/values-*.yaml"],
            "serverless": ["serverless.yml", "serverless.yaml", "serverless.ts"],
            "github_actions": [".github/workflows/*.yml", ".github/workflows/*.yaml"],
            "gitlab_ci": [".gitlab-ci.yml", ".gitlab-ci.yaml"],
            "circleci": [".circleci/config.yml"],
            "azure_pipelines": ["azure-pipelines.yml", "azure-pipelines.yaml"],
            "jenkins": ["Jenkinsfile", "Jenkinsfile.declarative"],
            "aws": ["template.yaml", "template.yml", "samconfig.toml"],
            "gcp": ["cloudbuild.yaml", "app.yaml", "app.yml"]
        }

        for category, patterns in deploy_patterns.items():
            for pattern in patterns:
                if "*" in pattern:
                    matches = list(self.project_path.rglob(pattern))
                else:
                    matches = [self.project_path / pattern] if (self.project_path / pattern).exists() else []

                for match in matches:
                    try:
                        rel_path = match.relative_to(self.project_path)
                        self.result.facts.append(InspectionFact(
                            category="deployment",
                            name=category,
                            value=str(rel_path),
                            confidence=FactConfidence.HIGH,
                            evidence=[f"Found deployment config: {rel_path}"],
                            source="static"
                        ))
                    except:
                        pass

    def _detect_docker_config(self):
        """Detect Docker configuration details."""
        dockerfile = self.project_path / "Dockerfile"
        if dockerfile.exists():
            try:
                content = dockerfile.read_text(encoding="utf-8", errors="ignore")
                lines = content.splitlines()

                base_image = None
                exposed_ports = []
                workdir = None
                user = None

                for line in lines:
                    line = line.strip()
                    if line.startswith("FROM "):
                        base_image = line[5:].strip()
                    elif line.startswith("EXPOSE "):
                        ports = line[7:].strip().split()
                        exposed_ports.extend(ports)
                    elif line.startswith("WORKDIR "):
                        workdir = line[8:].strip()
                    elif line.startswith("USER "):
                        user = line[5:].strip()

                self.result.facts.append(InspectionFact(
                    category="docker",
                    name="Dockerfile",
                    value=base_image,
                    confidence=FactConfidence.HIGH,
                    evidence=[f"Base: {base_image}", f"Ports: {exposed_ports}", f"Workdir: {workdir}", f"User: {user}"],
                    source="static"
                ))
            except Exception as e:
                self.result.errors.append(f"Failed to parse Dockerfile: {e}")

        # Docker Compose
        for compose_file in ["docker-compose.yml", "docker-compose.yaml"]:
            path = self.project_path / compose_file
            if path.exists():
                try:
                    import yaml
                    compose = yaml.safe_load(path.read_text())
                    services = list(compose.get("services", {}).keys())
                    self.result.facts.append(InspectionFact(
                        category="docker",
                        name="docker-compose",
                        value=f"{len(services)} services",
                        confidence=FactConfidence.HIGH,
                        evidence=[f"Services: {', '.join(services)}"],
                        source="static"
                    ))
                except Exception as e:
                    self.result.errors.append(f"Failed to parse {compose_file}: {e}")

    def _detect_ci_cd_config(self):
        """Detect CI/CD pipeline configuration."""
        ci_files = {
            ".github/workflows": "GitHub Actions",
            ".gitlab-ci.yml": "GitLab CI",
            ".circleci/config.yml": "CircleCI",
            "azure-pipelines.yml": "Azure Pipelines",
            "Jenkinsfile": "Jenkins",
            ".travis.yml": "Travis CI",
            "bitbucket-pipelines.yml": "Bitbucket Pipelines",
            ".drone.yml": "Drone CI",
            "cloudbuild.yaml": "Google Cloud Build",
            "appveyor.yml": "AppVeyor"
        }

        for pattern, name in ci_files.items():
            if "*" in pattern:
                matches = list(self.project_path.rglob(pattern))
            else:
                matches = [self.project_path / pattern] if (self.project_path / pattern).exists() else []

            for match in matches:
                try:
                    rel_path = match.relative_to(self.project_path)
                    self.result.facts.append(InspectionFact(
                        category="ci_cd",
                        name=name,
                        value=str(rel_path),
                        confidence=FactConfidence.HIGH,
                        evidence=[f"Found CI/CD config: {rel_path}"],
                        source="static"
                    ))
                except:
                    pass

    def _detect_test_files(self):
        """Detect test files and patterns."""
        test_patterns = {
            "python": ["test_*.py", "*_test.py", "tests/*.py", "test/*.py"],
            "javascript": ["*.test.js", "*.test.ts", "*.spec.js", "*.spec.ts", "__tests__/*.js", "__tests__/*.ts"],
            "go": ["*_test.go"],
            "rust": ["tests/*.rs", "*_test.rs"],
            "java": ["*Test.java", "*TestCase.java", "test/*Test.java"],
            "csharp": ["*Tests.cs", "*Test.cs", "Tests/*.cs"]
        }

        total_test_files = 0
        for lang, patterns in test_patterns.items():
            for pattern in patterns:
                matches = list(self.project_path.rglob(pattern))
                if matches:
                    total_test_files += len(matches)
                    self.result.facts.append(InspectionFact(
                        category="test_file",
                        name=f"{lang} test files",
                        value=str(len(matches)),
                        confidence=FactConfidence.HIGH,
                        evidence=[f"Found {len(matches)} files matching {pattern}"],
                        source="static"
                    ))

        if total_test_files == 0:
            self.result.unknown_facts.append("No test files detected")

    # ==========================================================================
    # Summary
    # ==========================================================================

    def _summarize_unknowns(self):
        """Summarize things we couldn't determine."""
        if not self.result.facts:
            self.result.unknown_facts.append("No facts could be determined from static analysis")

        # Check for critical unknowns
        has_language = any(f.category == "language" for f in self.result.facts)
        if not has_language:
            self.result.unknown_facts.append("Primary programming language undetermined")

        has_manifest = any(f.category == "manifest" for f in self.result.facts)
        if not has_manifest:
            self.result.unknown_facts.append("No recognized project manifests found")

        has_test = any(f.category in ["test_command", "test_file"] for f in self.result.facts)
        if not has_test:
            self.result.unknown_facts.append("No test configuration detected")


# ==============================================================================
# Public API
# ==============================================================================

def inspect_project(project_path: str) -> InspectionResult:
    """Main entry point for project inspection."""
    inspector = StaticInspector(Path(project_path))
    return inspector.inspect()

def inspect_project_to_json(project_path: str) -> str:
    """Inspect project and return JSON result."""
    result = inspect_project(project_path)
    return json.dumps(result.to_dict(), indent=2)


# ==============================================================================
# CLI Integration
# ==============================================================================

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = inspect_project(sys.argv[1])
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print("Usage: python -m asta.inspection <project_path>")