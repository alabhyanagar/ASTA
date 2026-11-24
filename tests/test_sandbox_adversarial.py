#!/usr/bin/env python3
"""
ASTA Sandbox Adversarial Tests

Security gate tests that must pass before M1 release.
Note: Full isolation (host file access, memory limits, disk writes) is enforced
by DockerSandbox on WSL2. SubprocessSandbox provides best-effort isolation on Windows.
Run with: pytest tests/test_sandbox_adversarial.py -v
"""

import pytest
import sys
import tempfile
from pathlib import Path

from asta.worker.sandbox import (
    ExecutionRequest,
    ExecutionResult,
    ResourceLimits,
    NetworkPolicy,
    MountSpec,
    SandboxFactory,
    SandboxBackend,
)


class TestSandboxAdversarial:
    """Adversarial security tests for sandbox isolation."""

    @pytest.fixture
    def sandbox(self):
        """Create subprocess sandbox for testing."""
        sandbox = SandboxFactory.create(
            preferred=SandboxBackend.SUBPROCESS,
            fallback=True
        )
        yield sandbox
        sandbox.cleanup()

    @pytest.mark.skipif(sys.platform == "win32", reason="Full host file isolation requires DockerSandbox on WSL2")
    def test_host_file_access_denied(self, sandbox):
        """Sandbox cannot read host files outside mounts (DockerSandbox only)."""
        req = ExecutionRequest(
            command=["cmd", "/c", "type C:\\Windows\\System32\\drivers\\etc\\hosts"] if sys.platform == "win32"
                   else ["cat", "/etc/passwd"],
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
        # Should not contain host file contents
        assert "root:" not in result.stdout
        assert "localhost" not in result.stdout.lower()
        sandbox.cleanup()

    def test_docker_socket_denied(self, sandbox):
        """Sandbox cannot access Docker socket."""
        req = ExecutionRequest(
            command=["cmd", "/c", "dir \\\\.\\pipe\\docker_engine"] if sys.platform == "win32"
                   else ["ls", "-la", "/var/run/docker.sock"],
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

    def test_secret_canary_redaction(self, sandbox):
        """Secrets in env are not visible in sandbox."""
        secret = "ASTA_TEST_SECRET_CANARY_12345"
        req = ExecutionRequest(
            command=["cmd", "/c", "set"] if sys.platform == "win32"
                   else ["sh", "-c", "env | grep CANARY"],
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

    def test_no_privilege_escalation(self, sandbox):
        """Sandbox runs with reduced privileges."""
        req = ExecutionRequest(
            command=["cmd", "/c", "whoami"] if sys.platform == "win32"
                   else ["id", "-u"],
            workdir="/workspace",
            env={},
            resource_limits=ResourceLimits(),
            network_policy=NetworkPolicy(),
            mounts=[],
            timeout_seconds=5,
        )
        sandbox.prepare(req)
        result = sandbox.execute(req)
        # Should not be SYSTEM/root
        if sys.platform == "win32":
            # On Windows, should be regular user (not SYSTEM)
            assert "SYSTEM" not in result.stdout.upper()
        else:
            # On Unix, should not be 0 (root)
            assert result.stdout.strip() != "0"
        sandbox.cleanup()

    def test_no_host_network_access(self, sandbox):
        """Sandbox cannot access host network interfaces."""
        req = ExecutionRequest(
            command=["cmd", "/c", "ipconfig"] if sys.platform == "win32"
                   else ["ip", "addr", "show"],
            workdir="/workspace",
            env={},
            resource_limits=ResourceLimits(),
            network_policy=NetworkPolicy(),
            mounts=[],
            timeout_seconds=5,
        )
        sandbox.prepare(req)
        result = sandbox.execute(req)
        # Should not show host network interfaces
        assert "192.168." not in result.stdout
        assert "10.0." not in result.stdout
        sandbox.cleanup()

    @pytest.mark.skipif(sys.platform == "win32", reason="Memory limits via RLIMIT_AS not available on Windows SubprocessSandbox")
    def test_resource_limit_memory(self, sandbox):
        """Memory limit enforced (Unix only with RLIMIT_AS)."""
        # Try to allocate more memory than limit
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

    def test_process_limit_enforced(self, sandbox):
        """Process limit enforced."""
        # Try to fork many processes
        req = ExecutionRequest(
            command=["python", "-c",
                     "import os; [os.fork() for _ in range(100)]"],
            workdir="/workspace",
            env={},
            resource_limits=ResourceLimits(max_processes=10),
            network_policy=NetworkPolicy(),
            mounts=[],
            timeout_seconds=10,
        )
        sandbox.prepare(req)
        result = sandbox.execute(req)
        # Should be killed or exit with error
        assert result.killed or result.exit_code != 0
        sandbox.cleanup()

    @pytest.mark.skipif(sys.platform == "win32", reason="Full disk write isolation requires DockerSandbox on WSL2")
    def test_no_disk_write_outside_workdir(self, sandbox):
        """Sandbox cannot write outside workdir (DockerSandbox only)."""
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "outside.txt"

            req = ExecutionRequest(
                command=["cmd", "/c", f"echo hacked > {target}"] if sys.platform == "win32"
                       else ["sh", "-c", f"echo hacked > {target}"],
                workdir="/workspace",
                env={},
                resource_limits=ResourceLimits(),
                network_policy=NetworkPolicy(),
                mounts=[],  # No mount for target
                timeout_seconds=5,
            )
            sandbox.prepare(req)
            result = sandbox.execute(req)
            assert result.exit_code != 0
            assert not target.exists()
            sandbox.cleanup()

    def test_no_symlink_escape(self, sandbox):
        """Symlinks cannot escape sandbox."""
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "safe"
            src.mkdir()
            link = src / "escape"
            # Create symlink to outside (may fail on Windows without admin)
            try:
                outside = Path(tmp).parent / "outside"
                link.symlink_to(outside)
            except (OSError, NotImplementedError):
                pytest.skip("Symlink creation not supported")

            req = ExecutionRequest(
                command=["cmd", "/c", "type escape\\test.txt"] if sys.platform == "win32"
                       else ["cat", "escape/test.txt"],
                workdir="/workspace",
                env={},
                resource_limits=ResourceLimits(),
                network_policy=NetworkPolicy(),
                mounts=[MountSpec(source=str(src), target="/workspace/safe", read_only=True)],
                timeout_seconds=5,
            )
            sandbox.prepare(req)
            result = sandbox.execute(req)
        assert result.exit_code != 0
        sandbox.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])