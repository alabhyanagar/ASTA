# Detailed Implementation Plan: Task 1 — Execution Sandboxing (`asta/worker/sandbox.py`)

---

## 1. Overview & Objectives

**Goal:** Implement a pluggable execution sandbox abstraction with two concrete backends:
- `DockerSandbox` — Primary production backend (full isolation via Linux containers on WSL2)
- `SubprocessSandbox` — Fallback backend (reduced isolation, no Docker required)

**Success Criteria:**
- All sandbox operations are deterministic and auditable
- Resource limits enforced (CPU, memory, disk, processes, wall-clock)
- Network deny-by-default with explicit allowlist
- Host credentials never leak into sandbox environment
- Cleanup guaranteed on success, failure, timeout, cancellation, or crash
- Interface supports async execution with progress callbacks

---

## 2. Architecture & Interface Design

### 2.1 Base Abstract Interface

```python
# asta/worker/sandbox.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable, Any
from enum import Enum

class SandboxBackend(str, Enum):
    DOCKER = "docker"
    SUBPROCESS = "subprocess"

@dataclass(frozen=True)
class ResourceLimits:
    cpu_cores: float = 2.0           # CPU quota (cores)
    memory_mb: int = 2048            # Memory limit (megabytes)
    disk_mb: int = 10240             # Disk limit (megabytes)
    max_processes: int = 50          # Process count limit
    wall_clock_seconds: int = 300    # Wall-clock timeout
    output_mb: int = 5               # Stdout/stderr capture limit

@dataclass(frozen=True)
class NetworkPolicy:
    enabled: bool = False
    allowed_hosts: List[str] = None  # Explicit allowlist (host:port or CIDR)
    allow_dns: bool = False          # Allow DNS resolution

@dataclass(frozen=True)
class MountSpec:
    source: str                      # Host path
    target: str                      # Container/sandbox path
    read_only: bool = True
    mount_type: str = "bind"         # bind, tmpfs, volume

@dataclass(frozen=True)
class ExecutionRequest:
    command: List[str]               # Command + args (argv style)
    workdir: str                     # Working directory inside sandbox
    env: Dict[str, str]              # Environment variables
    resource_limits: ResourceLimits
    network_policy: NetworkPolicy
    mounts: List[MountSpec]
    timeout_seconds: int             # Per-command timeout (≤ wall_clock_seconds)
    stdin_input: Optional[str] = None

@dataclass(frozen=True)
class ExecutionResult:
    exit_code: int                   # -1 if timed out / killed
    stdout: str                      # Truncated to output_mb
    stderr: str                      # Truncated to output_mb
    timed_out: bool
    killed: bool                     # True if killed for resource violation
    duration_seconds: float
    resource_usage: Dict[str, Any]   # Actual CPU, memory, disk, processes used
    artifacts: List[str]             # Paths to output artifacts (relative to workdir)

class ProgressCallback(Protocol):
    def __call__(self, phase: str, message: str, progress: float) -> None: ...

class BaseSandbox(ABC):
    """Abstract execution sandbox interface."""
    
    @property
    @abstractmethod
    def backend(self) -> SandboxBackend: ...
    
    @property
    @abstractmethod
    def is_available(self) -> bool: ...
    
    @abstractmethod
    def prepare(self, request: ExecutionRequest) -> None:
        """Validate request, create resources (volumes, networks, temp dirs)."""
    
    @abstractmethod
    def execute(
        self, 
        request: ExecutionRequest,
        progress: Optional[ProgressCallback] = None
    ) -> ExecutionResult: ...
    
    @abstractmethod
    def cleanup(self) -> None:
        """Release all resources (containers, volumes, networks, temp dirs). 
        Must be idempotent and safe to call multiple times."""
    
    @abstractmethod
    def get_sandbox_info(self) -> Dict[str, Any]:
        """Return diagnostic info: backend version, resource limits, sandbox ID."""
    
    # Context manager support
    def __enter__(self) -> 'BaseSandbox': ...
    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...
```

### 2.2 Factory & Configuration

```python
# asta/worker/sandbox.py (continued)

from asta.config import SandboxConfig  # To be defined in asta/config.py

class SandboxFactory:
    """Creates sandbox instances based on configuration and availability."""
    
    @staticmethod
    def create(
        preferred: SandboxBackend = SandboxBackend.DOCKER,
        config: Optional[SandboxConfig] = None,
        fallback: bool = True
    ) -> BaseSandbox:
        """Create sandbox, falling back if preferred unavailable."""
    
    @staticmethod
    def detect_available_backends() -> List[SandboxBackend]:
        """Detect which backends are available on this system."""
```

---

## 3. DockerSandbox Implementation Details

### 3.1 Container Configuration

```python
# asta/worker/docker_sandbox.py

import docker
import uuid
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from asta.worker.sandbox import (
    BaseSandbox, SandboxBackend, ExecutionRequest, ExecutionResult,
    ResourceLimits, NetworkPolicy, MountSpec, ProgressCallback
)

class DockerSandbox(BaseSandbox):
    """Docker-based execution sandbox with full isolation."""
    
    def __init__(
        self,
        image: str = "asta-worker:latest",
        docker_client: Optional[docker.DockerClient] = None,
        default_limits: Optional[ResourceLimits] = None,
        default_network: Optional[NetworkPolicy] = None,
        artifact_dir: Optional[Path] = None,
    ):
        self._image = image
        self._client = docker_client or docker.from_env()
        self._default_limits = default_limits or ResourceLimits()
        self._default_network = default_network or NetworkPolicy()
        self._artifact_dir = artifact_dir or Path(tempfile.gettempdir()) / "asta-artifacts"
        self._artifact_dir.mkdir(parents=True, exist_ok=True)
        
        self._container = None
        self._network = None
        self._volumes: List[str] = []
        self._temp_dirs: List[Path] = []
        self._sandbox_id = str(uuid.uuid4())[:8]
    
    @property
    def backend(self) -> SandboxBackend:
        return SandboxBackend.DOCKER
    
    @property
    def is_available(self) -> bool:
        try:
            self._client.ping()
            # Verify image exists or can be pulled
            self._client.images.get(self._image)
            return True
        except Exception:
            return False
```

### 3.2 Resource Limit Translation (Docker → cgroups)

| Sandbox Limit | Docker Parameter |
|---------------|------------------|
| `cpu_cores` | `cpu_quota` / `cpu_period` (quota = cores × 100000) |
| `memory_mb` | `mem_limit` (bytes), `memswap_limit` (same = no swap) |
| `disk_mb` | `--storage-opt size=` (requires overlay2) OR tmpfs mount with `size=` |
| `max_processes` | `pids_limit` |
| `wall_clock_seconds` | Managed by sandbox (not Docker — container timeout is separate) |
| `output_mb` | Managed by sandbox (stream truncation) |

### 3.3 Network Policy Implementation

```python
def _setup_network(self, policy: NetworkPolicy) -> Optional[str]:
    if not policy.enabled:
        return "none"  # --network none
    
    # Create isolated bridge network
    network_name = f"asta-{self._sandbox_id}"
    network = self._client.networks.create(
        name=network_name,
        driver="bridge",
        internal=True,  # No external access by default
        enable_ipv6=False,
    )
    self._network = network
    
    # If allowed_hosts specified, we need egress filtering
    # Option A: Use iptables in container (requires NET_ADMIN, CAP_NET_RAW)
    # Option B: Sidecar proxy (e.g., tinyproxy with ACL)
    # Option C: Host-level firewall rules (most reliable)
    # M1: Start with Option C — host iptables rules for allowed CIDRs
    if policy.allowed_hosts:
        self._install_egress_rules(policy.allowed_hosts)
    
    return network_name
```

### 3.4 Mount Handling

```python
def _prepare_mounts(self, mounts: List[MountSpec]) -> Dict[str, Dict]:
    docker_mounts = {}
    for mount in mounts:
        source = Path(mount.source).resolve()
        if not source.exists():
            raise ValueError(f"Mount source does not exist: {source}")
        
        docker_mounts[str(source)] = {
            "bind": mount.target,
            "mode": "ro" if mount.read_only else "rw",
        }
    
    # Always add ephemeral scratch volume for outputs
    scratch_dir = self._artifact_dir / f"scratch-{self._sandbox_id}"
    scratch_dir.mkdir(parents=True, exist_ok=True)
    self._temp_dirs.append(scratch_dir)
    docker_mounts[str(scratch_dir)] = {
        "bind": "/workspace/outputs",
        "mode": "rw",
    }
    
    return docker_mounts
```

### 3.5 Execution Flow

```python
def execute(self, request: ExecutionRequest, progress: ProgressCallback = None) -> ExecutionResult:
    self.prepare(request)
    
    # Build container config
    host_config = self._client.api.create_host_config(
        # Resource limits
        cpu_quota=int(request.resource_limits.cpu_cores * 100000),
        cpu_period=100000,
        mem_limit=f"{request.resource_limits.memory_mb}m",
        memswap_limit=f"{request.resource_limits.memory_mb}m",
        pids_limit=request.resource_limits.max_processes,
        
        # Network
        network_mode=self._network_name or "none",
        
        # Mounts
        mounts=self._docker_mounts,
        
        # Security
        read_only=True,  # Root filesystem read-only
        cap_drop=["ALL"],
        security_opt=["no-new-privileges:true"],
        user="1000:1000",  # Non-root
        
        # Working directory
        # Note: workdir set in container config, not host_config
    )
    
    # Create container
    container = self._client.containers.create(
        image=self._image,
        command=request.command,
        working_dir=request.workdir,
        environment=request.env,
        host_config=host_config,
        detach=True,
        stdin_open=bool(request.stdin_input),
    )
    self._container = container
    
    # Start with progress callback
    if progress:
        progress("starting", f"Container {container.short_id} starting", 0.1)
    
    container.start()
    
    # Stream logs with timeout enforcement
    return self._wait_and_collect(container, request, progress)
```

### 3.6 Timeout & Kill Handling

```python
def _wait_and_collect(self, container, request: ExecutionRequest, progress) -> ExecutionResult:
    import time
    import signal
    
    start_time = time.monotonic()
    deadline = start_time + request.timeout_seconds
    
    stdout_chunks = []
    stderr_chunks = []
    stdout_size = 0
    stderr_size = 0
    output_limit = request.resource_limits.output_mb * 1024 * 1024
    
    try:
        # Stream logs
        for log in container.logs(stdout=True, stderr=True, stream=True, follow=True):
            if time.monotonic() > deadline:
                self._kill_container(container, "timeout")
                return ExecutionResult(
                    exit_code=-1, stdout="".join(stdout_chunks), stderr="".join(stderr_chunks),
                    timed_out=True, killed=True, duration_seconds=time.monotonic() - start_time,
                    resource_usage=self._get_resource_usage(container), artifacts=[]
                )
            
            # Handle log format (Docker multiplexed stream)
            # Parse stdout/stderr frames, accumulate with size limit
            # ...
            
            if progress:
                elapsed = time.monotonic() - start_time
                progress("running", f"Running... {elapsed:.1f}s", min(elapsed / request.timeout_seconds, 0.9))
        
        # Container exited
        exit_code = container.wait()["StatusCode"]
        duration = time.monotonic() - start_time
        
        if progress:
            progress("completed", f"Exit code: {exit_code}", 1.0)
        
        return ExecutionResult(
            exit_code=exit_code,
            stdout="".join(stdout_chunks),
            stderr="".join(stderr_chunks),
            timed_out=False,
            killed=False,
            duration_seconds=duration,
            resource_usage=self._get_resource_usage(container),
            artifacts=self._collect_artifacts(),
        )
    
    except Exception as e:
        self._kill_container(container, f"error: {e}")
        raise
    finally:
        self.cleanup()
```

### 3.7 Cleanup (Idempotent, Guaranteed)

```python
def cleanup(self) -> None:
    # 1. Kill & remove container
    if self._container:
        try:
            self._container.kill()
        except: pass
        try:
            self._container.remove(v=True, force=True)
        except: pass
        self._container = None
    
    # 2. Remove network
    if self._network:
        try:
            self._network.remove()
        except: pass
        self._network = None
    
    # 3. Remove iptables egress rules
    self._remove_egress_rules()
    
    # 4. Cleanup temp directories (keep artifacts if needed)
    for temp_dir in self._temp_dirs:
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except: pass
    self._temp_dirs.clear()
    
    # 5. Cleanup volumes (if any created)
    for vol_name in self._volumes:
        try:
            self._client.volumes.get(vol_name).remove()
        except: pass
    self._volumes.clear()
```

---

## 4. SubprocessSandbox Implementation Details

### 4.1 Design Constraints

- **No Docker required** — runs on any Python 3.12+ environment
- **Reduced isolation** — process-group kill, working dir chroot-like containment, env scrubbing
- **Same interface** — drop-in replacement for DockerSandbox

### 4.2 Process Group Kill (Cross-Platform)

```python
# asta/worker/subprocess_sandbox.py

import subprocess
import os
import signal
import time
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

class SubprocessSandbox(BaseSandbox):
    """Subprocess-based sandbox with reduced isolation."""
    
    def __init__(
        self,
        default_limits: Optional[ResourceLimits] = None,
        artifact_dir: Optional[Path] = None,
    ):
        self._default_limits = default_limits or ResourceLimits()
        self._artifact_dir = artifact_dir or Path(tempfile.gettempdir()) / "asta-artifacts"
        self._artifact_dir.mkdir(parents=True, exist_ok=True)
        
        self._process = None
        self._temp_dirs: List[Path] = []
        self._sandbox_id = str(uuid.uuid4())[:8]
    
    @property
    def backend(self) -> SandboxBackend:
        return SandboxBackend.SUBPROCESS
    
    @property
    def is_available(self) -> bool:
        return True  # Always available
    
    def _scrub_environment(self, env: Dict[str, str]) -> Dict[str, str]:
        """Remove host credentials from environment."""
        scrubbed = {}
        blocked_patterns = [
            "SECRET", "TOKEN", "KEY", "PASSWORD", "CREDENTIAL",
            "AWS_", "AZURE_", "GCP_", "DOCKER_", "KUBE_",
            "SSH_", "GPG_", "PRIVATE", "ACCESS_", "CLIENT_"
        ]
        for key, value in env.items():
            if not any(pattern in key.upper() for pattern in blocked_patterns):
                scrubbed[key] = value
        # Add minimal safe defaults
        scrubbed.setdefault("PATH", "/usr/bin:/bin")
        scrubbed.setdefault("HOME", "/tmp")
        scrubbed.setdefault("USER", "asta")
        return scrubbed
    
    def _create_workdir_jail(self, workdir: str, mounts: List[MountSpec]) -> Path:
        """Create isolated working directory with bind-mounted sources."""
        jail_root = Path(tempfile.mkdtemp(prefix=f"asta-jail-{self._sandbox_id}-"))
        self._temp_dirs.append(jail_root)
        
        # Create workdir inside jail
        jailed_workdir = jail_root / "workspace"
        jailed_workdir.mkdir(parents=True)
        
        # Bind-mount sources (read-only where specified)
        for mount in mounts:
            source = Path(mount.source).resolve()
            target = jailed_workdir / mount.target.lstrip("/")
            target.parent.mkdir(parents=True, exist_ok=True)
            
            if mount.read_only:
                # Use bind mount read-only (Linux) or copy (fallback)
                try:
                    os.mount(str(source), str(target), None, os.MS_BIND | os.MS_RDONLY, "")
                except (AttributeError, OSError):
                    # Fallback: copy (not ideal but works)
                    shutil.copytree(source, target, dirs_exist_ok=True)
            else:
                try:
                    os.mount(str(source), str(target), None, os.MS_BIND, "")
                except (AttributeError, OSError):
                    shutil.copytree(source, target, dirs_exist_ok=True)
        
        return jailed_workdir
    
    def _kill_process_group(self, pid: int) -> bool:
        """Kill entire process group cross-platform."""
        try:
            if os.name == "posix":
                os.killpg(os.getpgid(pid), signal.SIGKILL)
            else:
                # Windows: use taskkill /T /F /PID
                subprocess.run(
                    ["taskkill", "/T", "/F", "/PID", str(pid)],
                    capture_output=True, timeout=5
                )
            return True
        except Exception:
            return False
```

### 4.3 Resource Limits (Best Effort)

| Limit | Subprocess Implementation |
|-------|---------------------------|
| CPU | `psutil.Process().cpu_affinity()` + `nice` (advisory) |
| Memory | `resource.setrlimit(resource.RLIMIT_AS, ...)` (Unix only) |
| Disk | Monitor via `psutil.disk_usage()` polling |
| Processes | `resource.setrlimit(resource.RLIMIT_NPROC, ...)` (Unix only) |
| Wall-clock | Threading.Timer → `_kill_process_group()` |
| Output | Stream truncation in reader threads |

---

## 5. Configuration Schema (`asta/config.py`)

```python
# asta/config.py (new file or extend existing)

from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path
from asta.worker.sandbox import SandboxBackend, ResourceLimits, NetworkPolicy

@dataclass
class SandboxConfig:
    # Backend selection
    preferred_backend: SandboxBackend = SandboxBackend.DOCKER
    allow_fallback: bool = True
    
    # Docker settings
    docker_image: str = "asta-worker:latest"
    docker_socket: str = "unix:///var/run/docker.sock"
    docker_pull_policy: str = "if_not_present"  # always, if_not_present, never
    
    # Default resource limits
    default_limits: ResourceLimits = field(default_factory=ResourceLimits)
    
    # Default network policy
    default_network: NetworkPolicy = field(default_factory=NetworkPolicy)
    
    # Artifact storage
    artifact_dir: Path = Path.home() / ".asta" / "artifacts"
    artifact_retention_days: int = 90
    
    # Security
    scrub_host_env: bool = True
    allowed_env_prefixes: List[str] = field(default_factory=lambda: ["ASTA_", "PYTHON"])
    
    # Timeouts
    container_create_timeout: int = 30
    container_start_timeout: int = 60
    
    @classmethod
    def from_toml(cls, path: Path) -> 'SandboxConfig': ...
    def to_toml(self, path: Path) -> None: ...
```

---

## 6. Worker Image (`asta/worker/Dockerfile`)

```dockerfile
# asta/worker/Dockerfile
FROM python:3.12-slim

# Install runtime dependencies only (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -g 1000 asta && useradd -u 1000 -g asta -m -s /bin/bash asta

# Set up workspace
WORKDIR /workspace
RUN chown asta:asta /workspace

# Copy only the worker entrypoint script
COPY --chown=asta:asta entrypoint.py /usr/local/bin/asta-worker-entrypoint
RUN chmod +x /usr/local/bin/asta-worker-entrypoint

USER asta
ENTRYPOINT ["python", "/usr/local/bin/asta-worker-entrypoint"]
```

```python
# asta/worker/entrypoint.py
"""Worker container entrypoint — executes command passed via docker run."""
import sys
import os
import subprocess

def main():
    # Command passed as docker run arguments
    cmd = sys.argv[1:] if len(sys.argv) > 1 else ["bash"]
    
    # Execute with same process group (for clean kill)
    os.setpgrp()
    result = subprocess.run(cmd, capture_output=False)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
```

---

## 7. Testing Strategy

### 7.1 Unit Tests (`tests/test_sandbox.py`)

```python
# tests/test_sandbox.py

import pytest
from asta.worker.sandbox import (
    BaseSandbox, DockerSandbox, SubprocessSandbox, SandboxFactory,
    ExecutionRequest, ExecutionResult, ResourceLimits, NetworkPolicy, MountSpec
)

class TestSandboxInterface:
    """Contract tests — both backends must pass."""
    
    @pytest.fixture(params=[SandboxBackend.DOCKER, SandboxBackend.SUBPROCESS])
    def sandbox(self, request):
        if request.param == SandboxBackend.DOCKER:
            s = DockerSandbox()
            if not s.is_available:
                pytest.skip("Docker not available")
            return s
        return SubprocessSandbox()
    
    def test_basic_execution(self, sandbox):
        req = ExecutionRequest(
            command=["echo", "hello"],
            workdir="/workspace",
            env={},
            resource_limits=ResourceLimits(),
            network_policy=NetworkPolicy(),
            mounts=[],
            timeout_seconds=10,
        )
        sandbox.prepare(req)
        result = sandbox.execute(req)
        assert result.exit_code == 0
        assert "hello" in result.stdout
        sandbox.cleanup()
    
    def test_timeout_enforcement(self, sandbox):
        req = ExecutionRequest(
            command=["sleep", "10"],
            workdir="/workspace",
            env={},
            resource_limits=ResourceLimits(),
            network_policy=NetworkPolicy(),
            mounts=[],
            timeout_seconds=1,
        )
        sandbox.prepare(req)
        result = sandbox.execute(req)
        assert result.timed_out
        assert result.killed
        sandbox.cleanup()
    
    def test_resource_limit_memory(self, sandbox):
        # Allocate memory exceeding limit
        req = ExecutionRequest(
            command=["python", "-c", "x = ' ' * 300_000_000"],  # ~300MB
            workdir="/workspace",
            env={},
            resource_limits=ResourceLimits(memory_mb=100),  # 100MB limit
            network_policy=NetworkPolicy(),
            mounts=[],
            timeout_seconds=10,
        )
        sandbox.prepare(req)
        result = sandbox.execute(req)
        # Should be killed or exit with OOM
        assert result.killed or result.exit_code != 0
        sandbox.cleanup()
    
    def test_network_deny_by_default(self, sandbox):
        req = ExecutionRequest(
            command=["python", "-c", "import urllib.request; urllib.request.urlopen('http://example.com')"],
            workdir="/workspace",
            env={},
            resource_limits=ResourceLimits(),
            network_policy=NetworkPolicy(enabled=False),  # Deny by default
            mounts=[],
            timeout_seconds=10,
        )
        sandbox.prepare(req)
        result = sandbox.execute(req)
        assert result.exit_code != 0  # Should fail (no network)
        sandbox.cleanup()
    
    def test_read_only_mount(self, sandbox):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "source"
            src.mkdir()
            (src / "file.txt").write_text("read-only")
            
            req = ExecutionRequest(
                command=["sh", "-c", "echo 'write' > /workspace/source/file.txt"],
                workdir="/workspace",
                env={},
                resource_limits=ResourceLimits(),
                network_policy=NetworkPolicy(),
                mounts=[MountSpec(source=str(src), target="/workspace/source", read_only=True)],
                timeout_seconds=10,
            )
            sandbox.prepare(req)
            result = sandbox.execute(req)
            assert result.exit_code != 0  # Write should fail
            assert (src / "file.txt").read_text() == "read-only"  # Unchanged
            sandbox.cleanup()
```

### 7.2 Integration Tests (`tests/test_execution_e2e.py`)

```python
# tests/test_execution_e2e.py

def test_full_pipeline_inspect_plan_run_report(tmp_path):
    """End-to-end: inspect -> plan -> approve -> run -> report"""
    # 1. Create sample project
    project = create_sample_fastapi_project(tmp_path)
    
    # 2. Run CLI commands via subprocess
    result = run_cli(["project", "add", str(project)])
    assert "Project created" in result.stdout
    
    result = run_cli(["sta", "inspect", str(project)])
    assert "fastapi" in result.stdout
    assert "pytest" in result.stdout
    
    result = run_cli(["sta", "plan", str(project)])
    assert "included" in result.stdout
    
    result = run_cli(["sta", "approve", str(project), "--confirm-all"])
    assert "approved" in result.stdout.lower()
    
    result = run_cli(["sta", "run", str(project)])
    assert result.exit_code == 0
    assert "PASSED" in result.stdout or "FAILED" in result.stdout  # Deterministic
    
    result = run_cli(["sta", "report", str(project)])
    assert "report" in result.stdout.lower()
```

### 7.3 Adversarial Tests (Security Gate)

```python
# tests/test_sandbox_adversarial.py

def test_host_file_access_denied(sandbox):
    """Container cannot read host files outside mounts."""
    req = ExecutionRequest(
        command=["cat", "/etc/passwd"],
        workdir="/workspace",
        env={},
        resource_limits=ResourceLimits(),
        network_policy=NetworkPolicy(),
        mounts=[],  # No mounts
        timeout_seconds=5,
    )
    sandbox.prepare(req)
    result = sandbox.execute(req)
    assert result.exit_code != 0
    assert "root:" not in result.stdout
    sandbox.cleanup()

def test_docker_socket_denied(sandbox):
    """Container cannot access Docker socket."""
    req = ExecutionRequest(
        command=["sh", "-c", "ls -la /var/run/docker.sock"],
        workdir="/workspace",
        env={},
        resource_limits=ResourceLimits(),
        network_policy=NetworkPolicy(),
        mounts=[],
        timeout_seconds=5,
    )
    sandbox.prepare(req)
    result = sandbox.execute(req)
    assert result.exit_code != 0
    sandbox.cleanup()

def test_secret_canary_redaction(sandbox):
    """Secrets in env are not visible in container."""
    secret = "ASTA_TEST_SECRET_CANARY_12345"
    req = ExecutionRequest(
        command=["sh", "-c", "env | grep CANARY"],
        workdir="/workspace",
        env={"ASTA_TEST_SECRET_CANARY_12345": secret},
        resource_limits=ResourceLimits(),
        network_policy=NetworkPolicy(),
        mounts=[],
        timeout_seconds=5,
    )
    sandbox.prepare(req)
    result = sandbox.execute(req)
    assert secret not in result.stdout
    assert secret not in result.stderr
    sandbox.cleanup()

def test_no_privilege_escalation(sandbox):
    """Container runs as non-root, cannot escalate."""
    req = ExecutionRequest(
        command=["id", "-u"],
        workdir="/workspace",
        env={},
        resource_limits=ResourceLimits(),
        network_policy=NetworkPolicy(),
        mounts=[],
        timeout_seconds=5,
    )
    sandbox.prepare(req)
    result = sandbox.execute(req)
    assert result.stdout.strip() == "1000"  # asta user UID
    sandbox.cleanup()
```

---

## 8. Implementation Order & Dependencies

| Step | File | Dependencies | Est. Effort |
|------|------|--------------|-------------|
| 1 | `asta/worker/sandbox.py` (base interface) | `asta.config` | 2h |
| 2 | `asta/worker/docker_sandbox.py` | `docker` package, `asta.config` | 6h |
| 3 | `asta/worker/subprocess_sandbox.py` | `psutil`, `resource` (stdlib) | 4h |
| 4 | `asta/worker/__init__.py` (exports) | Steps 1-3 | 0.5h |
| 5 | `asta/worker/Dockerfile` + `entrypoint.py` | None | 1h |
| 6 | `asta/config.py` (SandboxConfig) | None | 1h |
| 7 | Unit tests `tests/test_sandbox.py` | Steps 1-4 | 3h |
| 8 | Adversarial tests `tests/test_sandbox_adversarial.py` | Steps 1-4 | 2h |
| 9 | Integration test `tests/test_execution_e2e.py` | Full pipeline | 2h |

**Total: ~21.5 hours**

---

## 9. Acceptance Criteria (Gate C — Isolation)

From backlog `ASTA-074`:

> Pass adversarial isolation and target-boundary acceptance suite. Demonstrate:
> - Host-file/socket denial
> - No source writes
> - Resource caps
> - DNS rebinding
> - Direct IPv4/IPv6
> - Redirect
> - Local/private/link-local/metadata denial
> - Target allow case
> - Archive/path attacks
> - Oversized output
> - Cancellation
> - Cleanup
> - Secret-canary redaction
>
> If any critical case fails, disable project-code execution and release only read-only analysis/trusted-project mode.

---

## 10. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Docker not available on Windows without WSL2 | SubprocessSandbox fallback; clear error message |
| Docker Desktop licensing (Business vs Personal) | Document requirement; test on both |
| cgroups v1 vs v2 resource limit differences | Test on both; use `docker info --format '{{.CgroupDriver}}'` |
| Network namespace leakage | Use `--network none` + explicit bridge; verify with `ip netns` |
| Temp dir cleanup on crash | `try/finally` + `__exit__` + `atexit` registration |
| Output truncation loses critical evidence | Truncate at limit but preserve last N lines + "[TRUNCATED]" marker |
| Windows `taskkill` requires admin | Test without admin; use `CTRL_BREAK_EVENT` alternative |

---

## 11. Definition of Done

- [ ] `BaseSandbox` abstract interface defined with all required methods
- [ ] `DockerSandbox` implements full isolation (read-only, no network, resource limits, non-root)
- [ ] `SubprocessSandbox` implements best-effort isolation (process-group kill, env scrub, workdir jail)
- [ ] `SandboxFactory` creates appropriate backend with fallback
- [ ] Worker Docker image builds and runs (`asta-worker:latest`)
- [ ] All unit tests pass for both backends
- [ ] All adversarial security tests pass
- [ ] Integration test verifies full `inspect → plan → run → report` pipeline
- [ ] Resource limits enforced and reported in `ExecutionResult`
- [ ] Cleanup guaranteed on all exit paths (success, timeout, error, cancel)
- [ ] Configuration via `asta.toml` `[sandbox]` section

---

*Plan version: 1.0 | Date: 2026-11-24 | Author: Session planning*