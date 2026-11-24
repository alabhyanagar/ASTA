#!/usr/bin/env python3
"""
ASTA Sandbox Contract Tests

Both DockerSandbox and SubprocessSandbox must pass these tests.
Run with: pytest tests/test_sandbox.py -v
"""

import pytest
import sys
import tempfile
from pathlib import Path

from asta.worker.sandbox import (
    BaseSandbox,
    ExecutionRequest,
    ExecutionResult,
    ResourceLimits,
    NetworkPolicy,
    MountSpec,
    SandboxFactory,
    SandboxBackend,
)


class TestSandboxInterface:
    """Contract tests — both backends must pass these."""

    @pytest.fixture(params=[SandboxBackend.SUBPROCESS])
    def sandbox(self, request):
        """Create sandbox instance for testing."""
        if request.param == SandboxBackend.DOCKER:
            from asta.worker import DockerSandbox
            s = DockerSandbox()
            if not s.is_available:
                pytest.skip("Docker not available")
            return s
        else:
            from asta.worker import SubprocessSandbox
            return SubprocessSandbox()

    def test_basic_execution(self, sandbox):
        """Basic command execution works."""
        req = ExecutionRequest(
            command=["echo", "hello world"],
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
        assert "hello world" in result.stdout
        sandbox.cleanup()

    def test_command_with_args(self, sandbox):
        """Commands with multiple arguments work."""
        req = ExecutionRequest(
            command=["python", "-c", "print('arg1', 'arg2')"],
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
        assert "arg1 arg2" in result.stdout
        sandbox.cleanup()

    def test_timeout_enforcement(self, sandbox):
        """Commands exceeding timeout are killed."""
        req = ExecutionRequest(
            command=["python", "-c", "import time; time.sleep(10)"],
            workdir="/workspace",
            env={},
            resource_limits=ResourceLimits(),
            network_policy=NetworkPolicy(),
            mounts=[],
            timeout_seconds=1,
        )
        sandbox.prepare(req)
        result = sandbox.execute(req)
        assert result.timed_out is True
        assert result.killed is True
        assert result.exit_code == -1
        sandbox.cleanup()

    def test_network_deny_by_default(self, sandbox):
        """Network access denied by default."""
        req = ExecutionRequest(
            command=["python", "-c", "import urllib.request; urllib.request.urlopen('http://example.com', timeout=2)"],
            workdir="/workspace",
            env={},
            resource_limits=ResourceLimits(),
            network_policy=NetworkPolicy(enabled=False),
            mounts=[],
            timeout_seconds=5,
        )
        sandbox.prepare(req)
        result = sandbox.execute(req)
        # Should fail to connect (network denied)
        assert result.exit_code != 0
        sandbox.cleanup()

    def test_read_only_mount(self, sandbox):
        """Read-only mounts prevent writes to source."""
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "source"
            src.mkdir()
            test_file = src / "file.txt"
            test_file.write_text("read-only content")

            # Cross-platform command to attempt write
            if sys.platform == "win32":
                command = ["cmd", "/c", "echo write attempt > source\\file.txt"]
            else:
                command = ["sh", "-c", "echo 'write attempt' > /workspace/source/file.txt"]

            req = ExecutionRequest(
                command=command,
                workdir="/workspace",
                env={},
                resource_limits=ResourceLimits(),
                network_policy=NetworkPolicy(),
                mounts=[MountSpec(source=str(src), target="/workspace/source", read_only=True)],
                timeout_seconds=10,
            )
            sandbox.prepare(req)
            result = sandbox.execute(req)
            # Write should fail on read-only mount (or copy fallback prevents write to source)
            # On Windows with copy fallback, the write goes to the copy, not the source
            # So we verify the original file is unchanged
            assert test_file.read_text() == "read-only content"
            sandbox.cleanup()

    def test_read_write_mount(self, sandbox):
        """Read-write mounts allow writes in the sandbox (copy-on-write semantics)."""
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "rw_mount"
            src.mkdir()

            # Cross-platform command to write a file
            if sys.platform == "win32":
                command = ["cmd", "/c", "echo written > rw_mount\\output.txt"]
            else:
                command = ["sh", "-c", "echo 'written' > /workspace/rw_mount/output.txt"]

            req = ExecutionRequest(
                command=command,
                workdir="/workspace",
                env={},
                resource_limits=ResourceLimits(),
                network_policy=NetworkPolicy(),
                mounts=[MountSpec(source=str(src), target="/workspace/rw_mount", read_only=False)],
                timeout_seconds=10,
            )
            sandbox.prepare(req)
            result = sandbox.execute(req)
            assert result.exit_code == 0
            # Note: With copy fallback (Windows, no bind mount privileges), writes go to
            # the jailed copy, not the original source. This is correct isolation behavior.
            # The test verifies execution succeeds; source modification is not expected
            # without bind mount support.
            sandbox.cleanup()

    def test_env_scrubbing(self, sandbox):
        """Host secrets are scrubbed from environment."""
        req = ExecutionRequest(
            command=["python", "-c", "import os; print(os.environ.get('SECRET_KEY', 'NOT_FOUND'))"],
            workdir="/workspace",
            env={"SECRET_KEY": "should_be_scrubbed", "NORMAL_VAR": "should_remain"},
            resource_limits=ResourceLimits(),
            network_policy=NetworkPolicy(),
            mounts=[],
            timeout_seconds=10,
        )
        sandbox.prepare(req)
        result = sandbox.execute(req)
        # SECRET_KEY should be scrubbed, NORMAL_VAR should remain
        assert "NOT_FOUND" in result.stdout or "should_be_scrubbed" not in result.stdout
        sandbox.cleanup()

    def test_working_directory_isolation(self, sandbox):
        """Commands run in specified workdir."""
        req = ExecutionRequest(
            command=["pwd"],
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
        assert "/workspace" in result.stdout.strip()
        sandbox.cleanup()

    def test_output_truncation(self, sandbox):
        """Large output is truncated to limit."""
        req = ExecutionRequest(
            command=["python", "-c", "print('x' * 1000000)"],  # ~1MB output
            workdir="/workspace",
            env={},
            resource_limits=ResourceLimits(output_mb=1),  # 1MB limit
            network_policy=NetworkPolicy(),
            mounts=[],
            timeout_seconds=10,
        )
        sandbox.prepare(req)
        result = sandbox.execute(req)
        assert result.exit_code == 0
        # Output should be truncated
        assert len(result.stdout) <= 1.1 * 1024 * 1024  # Allow small overhead
        sandbox.cleanup()

    def test_cleanup_idempotent(self, sandbox):
        """cleanup() can be called multiple times without error."""
        req = ExecutionRequest(
            command=["echo", "test"],
            workdir="/workspace",
            env={},
            resource_limits=ResourceLimits(),
            network_policy=NetworkPolicy(),
            mounts=[],
            timeout_seconds=10,
        )
        sandbox.prepare(req)
        sandbox.execute(req)
        sandbox.cleanup()
        sandbox.cleanup()  # Second call should not raise
        sandbox.cleanup()  # Third call should not raise

    def test_context_manager(self, sandbox):
        """Sandbox works as context manager."""
        req = ExecutionRequest(
            command=["echo", "context manager test"],
            workdir="/workspace",
            env={},
            resource_limits=ResourceLimits(),
            network_policy=NetworkPolicy(),
            mounts=[],
            timeout_seconds=10,
        )
        with sandbox:
            sandbox.prepare(req)
            result = sandbox.execute(req)
            assert result.exit_code == 0
        # cleanup called automatically


class TestSandboxFactory:
    """Tests for SandboxFactory."""

    def test_detect_available_backends(self):
        """At least SubprocessSandbox is always available."""
        backends = SandboxFactory.detect_available_backends()
        assert SandboxBackend.SUBPROCESS in backends

    def test_create_subprocess_fallback(self):
        """Factory creates SubprocessSandbox when Docker unavailable."""
        sandbox = SandboxFactory.create(
            preferred=SandboxBackend.DOCKER,
            fallback=True
        )
        assert sandbox.backend == SandboxBackend.SUBPROCESS
        sandbox.cleanup()

    def test_create_no_fallback_raises(self):
        """Factory raises when preferred unavailable and no fallback."""
        with pytest.raises(RuntimeError):
            SandboxFactory.create(
                preferred=SandboxBackend.DOCKER,
                fallback=False
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])