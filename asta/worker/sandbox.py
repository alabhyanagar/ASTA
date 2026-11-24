#!/usr/bin/env python3
"""
ASTA Worker Sandbox — Abstract Interface

Pluggable execution sandbox abstraction with two backends:
- DockerSandbox: Full isolation via Linux containers (production)
- SubprocessSandbox: Reduced isolation, no Docker required (fallback)

All implementations must guarantee:
- Deterministic resource limits (CPU, memory, disk, processes, wall-clock)
- Network deny-by-default with explicit allowlist
- Host credential scrubbing from environment
- Idempotent cleanup on all exit paths
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol
from typing_extensions import runtime_checkable


class SandboxBackend(str, Enum):
    """Supported sandbox backends."""
    DOCKER = "docker"
    SUBPROCESS = "subprocess"


@dataclass(frozen=True)
class ResourceLimits:
    """Resource limits for sandbox execution."""
    cpu_cores: float = 2.0           # CPU quota (cores)
    memory_mb: int = 2048            # Memory limit (megabytes)
    disk_mb: int = 10240             # Disk limit (megabytes)
    max_processes: int = 50          # Process count limit
    wall_clock_seconds: int = 300    # Wall-clock timeout
    output_mb: int = 5               # Stdout/stderr capture limit (megabytes)


@dataclass(frozen=True)
class NetworkPolicy:
    """Network access policy for sandbox."""
    enabled: bool = False
    allowed_hosts: List[str] = field(default_factory=list)  # Explicit allowlist (host:port or CIDR)
    allow_dns: bool = False          # Allow DNS resolution


@dataclass(frozen=True)
class MountSpec:
    """Mount specification for sandbox."""
    source: str                      # Host path
    target: str                      # Container/sandbox path
    read_only: bool = True
    mount_type: str = "bind"         # bind, tmpfs, volume


@dataclass(frozen=True)
class ExecutionRequest:
    """Request to execute a command in the sandbox."""
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
    """Result of sandbox execution."""
    exit_code: int                   # -1 if timed out / killed
    stdout: str                      # Truncated to output_mb
    stderr: str                      # Truncated to output_mb
    timed_out: bool
    killed: bool                     # True if killed for resource violation
    duration_seconds: float
    resource_usage: Dict[str, Any]   # Actual CPU, memory, disk, processes used
    artifacts: List[str]             # Paths to output artifacts (relative to workdir)


@runtime_checkable
class ProgressCallback(Protocol):
    """Progress callback protocol for long-running executions."""
    def __call__(self, phase: str, message: str, progress: float) -> None: ...


class BaseSandbox(ABC):
    """Abstract execution sandbox interface.

    All concrete implementations must provide:
    - Resource limit enforcement
    - Network isolation (deny-by-default)
    - Host credential scrubbing
    - Guaranteed cleanup on all exit paths
    """

    def __init__(self) -> None:
        self._sandbox_id = str(uuid.uuid4())[:8]
        self._prepared = False

    @property
    @abstractmethod
    def backend(self) -> SandboxBackend:
        """Return the backend type."""
        ...

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this backend is available on the current system."""
        ...

    @property
    def sandbox_id(self) -> str:
        """Unique identifier for this sandbox instance."""
        return self._sandbox_id

    @property
    def is_prepared(self) -> bool:
        """Whether prepare() has been called successfully."""
        return self._prepared

    @abstractmethod
    def prepare(self, request: ExecutionRequest) -> None:
        """Validate request and create resources (volumes, networks, temp dirs).

        Must be called before execute(). Validates:
        - Command exists and is executable
        - Workdir is within allowed paths
        - Mounts exist and are accessible
        - Resource limits are within backend capabilities
        - Network policy is enforceable

        Raises:
            ValueError: If request is invalid
            RuntimeError: If resource creation fails
        """
        ...

    @abstractmethod
    def execute(
        self,
        request: ExecutionRequest,
        progress: Optional[ProgressCallback] = None
    ) -> ExecutionResult:
        """Execute the prepared command in the sandbox.

        Args:
            request: The execution request (must match prepared request)
            progress: Optional callback for progress updates

        Returns:
            ExecutionResult with exit code, output, resource usage, artifacts

        Raises:
            RuntimeError: If sandbox not prepared or execution fails
            TimeoutError: If execution exceeds timeout
        """
        ...

    @abstractmethod
    def cleanup(self) -> None:
        """Release all resources (containers, volumes, networks, temp dirs).

        Must be:
        - Idempotent (safe to call multiple times)
        - Safe to call after failed prepare/execute
        - Guaranteed to not raise exceptions
        """
        ...

    @abstractmethod
    def get_sandbox_info(self) -> Dict[str, Any]:
        """Return diagnostic information about the sandbox.

        Returns:
            Dict with keys: backend, sandbox_id, version, limits, status
        """
        ...

    # Context manager support for guaranteed cleanup
    def __enter__(self) -> BaseSandbox:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.cleanup()

    @staticmethod
    def _validate_request(request: ExecutionRequest) -> None:
        """Common request validation for all backends."""
        if not request.command:
            raise ValueError("Command cannot be empty")

        if not request.workdir or not request.workdir.startswith("/"):
            raise ValueError("Workdir must be an absolute path")

        if request.timeout_seconds <= 0:
            raise ValueError("Timeout must be positive")

        if request.timeout_seconds > request.resource_limits.wall_clock_seconds:
            raise ValueError("Command timeout cannot exceed wall-clock limit")

        if request.resource_limits.output_mb <= 0:
            raise ValueError("Output limit must be positive")

        # Validate mounts
        for mount in request.mounts:
            if not mount.source or not mount.target:
                raise ValueError("Mount source and target cannot be empty")
            if not mount.target.startswith("/"):
                raise ValueError("Mount target must be absolute path")

    @staticmethod
    def _scrub_environment(env: Dict[str, str]) -> Dict[str, str]:
        """Remove host credentials from environment variables.

        Scrubs variables matching sensitive patterns while preserving
        safe defaults for execution.
        """
        scrubbed = {}
        blocked_patterns = [
            "SECRET", "TOKEN", "KEY", "PASSWORD", "CREDENTIAL",
            "AWS_", "AZURE_", "GCP_", "DOCKER_", "KUBE_",
            "SSH_", "GPG_", "PRIVATE", "ACCESS_", "CLIENT_",
            "AUTH_", "BEARER", "OAUTH", "JWT", "API_KEY",
        ]

        for key, value in env.items():
            upper_key = key.upper()
            if not any(pattern in upper_key for pattern in blocked_patterns):
                scrubbed[key] = value

        # Ensure minimal safe environment
        scrubbed.setdefault("PATH", "/usr/bin:/bin")
        scrubbed.setdefault("HOME", "/tmp")
        scrubbed.setdefault("USER", "asta")
        scrubbed.setdefault("LANG", "C.UTF-8")
        scrubbed.setdefault("LC_ALL", "C.UTF-8")

        return scrubbed


class SandboxFactory:
    """Factory for creating sandbox instances."""

    _docker_sandbox_class = None
    _subprocess_sandbox_class = None

    @classmethod
    def _get_docker_sandbox(cls):
        """Lazy import to avoid Docker dependency if not used."""
        if cls._docker_sandbox_class is None:
            from asta.worker.docker_sandbox import DockerSandbox
            cls._docker_sandbox_class = DockerSandbox
        return cls._docker_sandbox_class

    @classmethod
    def _get_subprocess_sandbox(cls):
        """Lazy import for subprocess sandbox."""
        if cls._subprocess_sandbox_class is None:
            from asta.worker.subprocess_sandbox import SubprocessSandbox
            cls._subprocess_sandbox_class = SubprocessSandbox
        return cls._subprocess_sandbox_class

    @classmethod
    def create(
        cls,
        preferred: SandboxBackend = SandboxBackend.DOCKER,
        config: Optional[Any] = None,  # SandboxConfig when available
        fallback: bool = True,
        **kwargs
    ) -> BaseSandbox:
        """Create sandbox instance, falling back if preferred unavailable.

        Args:
            preferred: Preferred backend
            config: Optional sandbox configuration
            fallback: Whether to fall back to alternative backend
            **kwargs: Backend-specific options

        Returns:
            BaseSandbox instance

        Raises:
            RuntimeError: If no backend is available
        """
        if preferred == SandboxBackend.DOCKER:
            docker_class = cls._get_docker_sandbox()
            sandbox = docker_class(**kwargs)
            if sandbox.is_available:
                return sandbox
            if not fallback:
                raise RuntimeError("Docker backend requested but not available")

        # Fallback to subprocess
        subprocess_class = cls._get_subprocess_sandbox()
        sandbox = subprocess_class(**kwargs)
        if sandbox.is_available:
            return sandbox

        raise RuntimeError("No sandbox backend available")

    @classmethod
    def detect_available_backends(cls) -> List[SandboxBackend]:
        """Detect which backends are available on this system."""
        available = []

        try:
            docker_class = cls._get_docker_sandbox()
            if docker_class().is_available:
                available.append(SandboxBackend.DOCKER)
        except Exception:
            pass

        try:
            subprocess_class = cls._get_subprocess_sandbox()
            if subprocess_class().is_available:
                available.append(SandboxBackend.SUBPROCESS)
        except Exception:
            pass

        return available


__all__ = [
    "SandboxBackend",
    "ResourceLimits",
    "NetworkPolicy",
    "MountSpec",
    "ExecutionRequest",
    "ExecutionResult",
    "ProgressCallback",
    "BaseSandbox",
    "SandboxFactory",
]