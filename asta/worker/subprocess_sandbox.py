#!/usr/bin/env python3
"""
ASTA Subprocess Sandbox — Fallback Execution Backend

Reduced isolation for environments without Docker.
Implements: process-group kill, working dir jail, env scrubbing,
best-effort resource limits (RLIMIT on Unix, polling on Windows).
"""

from __future__ import annotations

import atexit
import logging
import os
import shlex
import signal
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import resource
    RESOURCE_AVAILABLE = True
except ImportError:
    RESOURCE_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from asta.worker.sandbox import (
    BaseSandbox,
    ExecutionRequest,
    ExecutionResult,
    MountSpec,
    NetworkPolicy,
    ProgressCallback,
    ResourceLimits,
    SandboxBackend,
)

logger = logging.getLogger(__name__)


class SubprocessSandbox(BaseSandbox):
    """Subprocess-based sandbox with reduced isolation.

    Provides best-effort isolation:
    - Process group kill (SIGKILL / taskkill /T /F)
    - Working directory jail via bind mounts or copy fallback
    - Environment scrubbing
    - Resource limits via RLIMIT (Unix) or psutil polling (Windows)
    """

    def __init__(
        self,
        default_limits: Optional[ResourceLimits] = None,
        artifact_dir: Optional[Path] = None,
    ):
        super().__init__()
        self._default_limits = default_limits or ResourceLimits()
        self._artifact_dir = artifact_dir or Path.home() / ".asta" / "artifacts"
        self._artifact_dir.mkdir(parents=True, exist_ok=True)

        # Runtime state
        self._process: Optional[subprocess.Popen] = None
        self._process_group_id: Optional[int] = None
        self._temp_dirs: List[Path] = []
        self._prepared_request: Optional[ExecutionRequest] = None
        self._jailed_workdir: Optional[Path] = None
        self._stdout_thread: Optional[threading.Thread] = None
        self._stderr_thread: Optional[threading.Thread] = None
        self._stdout_chunks: List[str] = []
        self._stderr_chunks: List[str] = []
        self._stdout_size = 0
        self._stderr_size = 0
        self._output_lock = threading.Lock()
        self._deadline: Optional[float] = None
        self._timed_out = False
        self._killed = False

        # Register cleanup on interpreter exit
        atexit.register(self.cleanup)

    @property
    def backend(self) -> SandboxBackend:
        return SandboxBackend.SUBPROCESS

    @property
    def is_available(self) -> bool:
        """Subprocess sandbox is always available."""
        return True

    def get_sandbox_info(self) -> Dict[str, Any]:
        info = {
            "backend": self.backend.value,
            "sandbox_id": self.sandbox_id,
            "prepared": self._prepared,
            "psutil_available": PSUTIL_AVAILABLE,
            "platform": sys.platform,
            "temp_dirs": [str(p) for p in self._temp_dirs],
            "jailed_workdir": str(self._jailed_workdir) if self._jailed_workdir else None,
        }
        if self._process:
            info["pid"] = self._process.pid
            info["process_group"] = self._process_group_id
        return info

    def prepare(self, request: ExecutionRequest) -> None:
        """Validate request and create working directory jail."""
        # Run common validation
        self._validate_request(request)

        # Validate mounts exist
        for mount in request.mounts:
            source = Path(mount.source).resolve()
            if not source.exists():
                raise ValueError(f"Mount source does not exist: {source}")

        # Create working directory jail
        self._jailed_workdir = self._create_workdir_jail(
            request.workdir,
            request.mounts
        )

        # Store prepared request for execute()
        self._prepared_request = request
        self._prepared = True

        logger.info(f"Subprocess sandbox {self.sandbox_id} prepared: jailed_workdir={self._jailed_workdir}")

    def execute(
        self,
        request: ExecutionRequest,
        progress: Optional[ProgressCallback] = None
    ) -> ExecutionResult:
        """Execute the prepared command in a jailed subprocess."""
        if not self._prepared or self._prepared_request != request:
            raise RuntimeError("Sandbox not prepared for this request. Call prepare() first.")

        if progress:
            progress("starting", f"Preparing jailed environment", 0.05)

        # Scrub environment
        scrubbed_env = self._scrub_environment(request.env)

        # Apply resource limits (best effort)
        self._apply_resource_limits(request.resource_limits)

        # Set deadline
        self._deadline = time.monotonic() + request.timeout_seconds
        self._timed_out = False
        self._killed = False
        self._stdout_chunks.clear()
        self._stderr_chunks.clear()
        self._stdout_size = 0
        self._stderr_size = 0

        output_limit = request.resource_limits.output_mb * 1024 * 1024

        # Start process in new process group
        start_time = time.monotonic()

        if progress:
            progress("starting", f"Starting process group", 0.1)

        try:
            self._process = self._start_process(request, scrubbed_env)
            self._process_group_id = self._get_process_group_id(self._process.pid)
        except Exception as e:
            raise RuntimeError(f"Failed to start process: {e}")

        if progress:
            progress("running", f"Process {self._process.pid} running", 0.15)

        # Start reader threads for stdout/stderr
        self._stdout_thread = threading.Thread(
            target=self._read_stream,
            args=(self._process.stdout, True, output_limit),
            daemon=True
        )
        self._stderr_thread = threading.Thread(
            target=self._read_stream,
            args=(self._process.stderr, False, output_limit),
            daemon=True
        )
        self._stdout_thread.start()
        self._stderr_thread.start()

        # Wait with timeout enforcement
        return self._wait_and_collect(request, start_time, progress)

    def cleanup(self) -> None:
        """Release all resources. Idempotent and exception-safe."""
        # 1. Kill process group if running
        if self._process and self._process.poll() is None:
            self._kill_process_group(self._process_group_id)
            try:
                self._process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                pass

        # 2. Wait for reader threads
        for thread in (self._stdout_thread, self._stderr_thread):
            if thread and thread.is_alive():
                thread.join(timeout=1)

        # 3. Cleanup temp directories (including jailed workdir)
        for temp_dir in self._temp_dirs:
            try:
                self._cleanup_mounts(temp_dir)
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass
        self._temp_dirs.clear()
        self._jailed_workdir = None

        self._prepared = False
        self._prepared_request = None
        self._process = None
        self._process_group_id = None
        logger.debug(f"Subprocess sandbox {self.sandbox_id} cleaned up")

    # =========================================================================
    # Private Implementation Methods
    # =========================================================================

    def _create_workdir_jail(self, workdir: str, mounts: List[MountSpec]) -> Path:
        """Create isolated working directory with bind-mounted sources."""
        # Create jail root in temp
        jail_root = Path(tempfile.mkdtemp(prefix=f"asta-jail-{self.sandbox_id}-"))
        self._temp_dirs.append(jail_root)

        # Create workdir inside jail
        # workdir is like "/workspace" - make it relative
        rel_workdir = workdir.lstrip("/")
        jailed_workdir = jail_root / rel_workdir
        jailed_workdir.mkdir(parents=True, exist_ok=True)

        # Bind-mount or copy sources
        for mount in mounts:
            source = Path(mount.source).resolve()
            # Mount target is absolute path inside sandbox (e.g., "/workspace/rw_mount")
            # We need to map it relative to the workdir, not the jail root
            # So "/workspace/rw_mount" with workdir="/workspace" -> "rw_mount"
            target_rel = mount.target.lstrip("/")
            if target_rel.startswith(rel_workdir + "/"):
                target_rel = target_rel[len(rel_workdir) + 1:]
            elif target_rel == rel_workdir:
                target_rel = "."
            target = jailed_workdir / target_rel
            target.parent.mkdir(parents=True, exist_ok=True)

            if sys.platform == "linux" and mount.read_only:
                # Linux: try bind mount read-only
                try:
                    # Requires root/CAP_SYS_ADMIN - usually not available
                    # Fall back to copy for now
                    raise OSError("Bind mount requires privileges")
                except (OSError, PermissionError):
                    # Fallback: copy
                    self._copy_tree(source, target)
            else:
                # Copy for Windows, non-read-only, or fallback
                self._copy_tree(source, target)

        return jailed_workdir

    def _copy_tree(self, src: Path, dst: Path) -> None:
        """Copy directory tree, handling existing destinations."""
        import shutil
        if dst.exists():
            if dst.is_dir():
                shutil.rmtree(dst)
            else:
                dst.unlink()
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    def _cleanup_mounts(self, jail_root: Path) -> None:
        """Unmount any bind mounts (Linux)."""
        if sys.platform == "linux":
            try:
                # Find and unmount any bind mounts under jail_root
                import subprocess
                result = subprocess.run(
                    ["findmnt", "-n", "-o", "TARGET", str(jail_root)],
                    capture_output=True, text=True
                )
                for line in result.stdout.strip().split("\n"):
                    if line.startswith(str(jail_root)):
                        subprocess.run(["umount", line], capture_output=True)
            except Exception:
                pass

    def _apply_resource_limits(self, limits: ResourceLimits) -> None:
        """Apply resource limits best-effort."""
        if RESOURCE_AVAILABLE and sys.platform != "win32":
            try:
                # Memory limit (virtual memory)
                if limits.memory_mb > 0:
                    mem_bytes = limits.memory_mb * 1024 * 1024
                    resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))

                # Process limit
                if limits.max_processes > 0:
                    resource.setrlimit(resource.RLIMIT_NPROC, (limits.max_processes, limits.max_processes))

                # CPU time (soft limit)
                if limits.wall_clock_seconds > 0:
                    resource.setrlimit(resource.RLIMIT_CPU, (limits.wall_clock_seconds, limits.wall_clock_seconds + 1))

            except (ValueError, OSError) as e:
                logger.debug(f"Could not set rlimit: {e}")
        else:
            # Windows or no resource module: limits enforced via polling in _monitor_resources
            logger.debug("Resource limits enforced via polling (Windows or no resource module)")

    def _start_process(self, request: ExecutionRequest, env: Dict[str, str]) -> subprocess.Popen:
        """Start process in new process group."""
        # Convert workdir to jailed path
        rel_workdir = request.workdir.lstrip("/")
        jailed_workdir = str(self._jailed_workdir)

        if sys.platform == "win32":
            # Windows: CREATE_NEW_PROCESS_GROUP
            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP
            self._process = subprocess.Popen(
                request.command,
                cwd=jailed_workdir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE if request.stdin_input else None,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=creation_flags,
            )
        else:
            # Unix: setpgid in preexec_fn
            def preexec():
                os.setpgrp()
                # Reset signal handlers
                signal.signal(signal.SIGINT, signal.SIG_DFL)
                signal.signal(signal.SIGTERM, signal.SIG_DFL)

            self._process = subprocess.Popen(
                request.command,
                cwd=jailed_workdir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE if request.stdin_input else None,
                text=True,
                encoding="utf-8",
                errors="replace",
                preexec_fn=preexec,
            )

        # Send stdin if provided
        if request.stdin_input and self._process.stdin:
            try:
                self._process.stdin.write(request.stdin_input)
                self._process.stdin.close()
            except Exception:
                pass

        return self._process

    def _get_process_group_id(self, pid: int) -> int:
        """Get process group ID for killing."""
        if sys.platform == "win32":
            return pid  # On Windows, we use the PID with taskkill /T
        try:
            return os.getpgid(pid)
        except Exception:
            return pid

    def _read_stream(self, stream, is_stdout: bool, output_limit: int) -> None:
        """Read stream in background thread with size limiting."""
        if not stream:
            return

        chunks = self._stdout_chunks if is_stdout else self._stderr_chunks
        size_var = "_stdout_size" if is_stdout else "_stderr_size"

        try:
            for line in stream:
                with self._output_lock:
                    current_size = getattr(self, size_var)
                    if current_size + len(line) <= output_limit:
                        chunks.append(line)
                        setattr(self, size_var, current_size + len(line))
                    elif current_size < output_limit:
                        remaining = output_limit - current_size
                        chunks.append(line[:remaining] + "\n[TRUNCATED]")
                        setattr(self, size_var, output_limit)
                        break
                    else:
                        break
        except Exception:
            pass

    def _wait_and_collect(
        self,
        request: ExecutionRequest,
        start_time: float,
        progress: Optional[ProgressCallback]
    ) -> ExecutionResult:
        """Wait for process with timeout and resource monitoring."""
        timeout = request.timeout_seconds
        poll_interval = 0.1

        while True:
            # Check if process exited
            exit_code = self._process.poll()
            if exit_code is not None:
                break

            # Check timeout
            if time.monotonic() >= self._deadline:
                self._timed_out = True
                self._kill_process_group(self._process_group_id)
                self._killed = True
                break

            # Check resource limits (Windows/monitoring)
            if sys.platform == "win32" and PSUTIL_AVAILABLE:
                self._monitor_resources(request.resource_limits)

            # Progress callback
            if progress:
                elapsed = time.monotonic() - start_time
                progress("running", f"Running... {elapsed:.1f}s", min(elapsed / timeout, 0.9))

            time.sleep(poll_interval)

        # Wait for reader threads
        for thread in (self._stdout_thread, self._stderr_thread):
            if thread and thread.is_alive():
                thread.join(timeout=1)

        duration = time.monotonic() - start_time

        # Get final exit code
        if self._timed_out:
            exit_code = -1
        else:
            exit_code = self._process.returncode if self._process.returncode is not None else -1

        if progress:
            status = "timed out" if self._timed_out else f"exit code {exit_code}"
            progress("completed", f"Process {status}", 1.0)

        # Collect resource usage
        resource_usage = self._collect_resource_usage()

        return ExecutionResult(
            exit_code=exit_code,
            stdout="".join(self._stdout_chunks),
            stderr="".join(self._stderr_chunks),
            timed_out=self._timed_out,
            killed=self._killed,
            duration_seconds=duration,
            resource_usage=resource_usage,
            artifacts=[],  # Subprocess sandbox doesn't have separate artifact dir
        )

    def _kill_process_group(self, pgid: Optional[int]) -> bool:
        """Kill entire process group cross-platform."""
        if pgid is None:
            return False

        try:
            if sys.platform == "win32":
                # Windows: taskkill /T /F /PID <pgid>
                subprocess.run(
                    ["taskkill", "/T", "/F", "/PID", str(pgid)],
                    capture_output=True, timeout=5
                )
            else:
                # Unix: killpg with SIGKILL
                os.killpg(pgid, signal.SIGKILL)
            logger.warning(f"Killed process group {pgid}")
            return True
        except Exception as e:
            logger.error(f"Failed to kill process group {pgid}: {e}")
            return False

    def _monitor_resources(self, limits: ResourceLimits) -> None:
        """Monitor resource usage and kill if exceeded (Windows/psutil)."""
        if not PSUTIL_AVAILABLE or not self._process:
            return

        try:
            proc = psutil.Process(self._process.pid)

            # Memory
            mem_mb = proc.memory_info().rss / 1024 / 1024
            if mem_mb > limits.memory_mb:
                logger.warning(f"Memory limit exceeded: {mem_mb:.1f}MB > {limits.memory_mb}MB")
                self._kill_process_group(self._process_group_id)
                self._killed = True
                return

            # CPU time
            cpu_time = proc.cpu_times().user + proc.cpu_times().system
            if cpu_time > limits.wall_clock_seconds:
                logger.warning(f"CPU time limit exceeded: {cpu_time:.1f}s > {limits.wall_clock_seconds}s")
                self._kill_process_group(self._process_group_id)
                self._killed = True
                return

            # Process count
            children = proc.children(recursive=True)
            if len(children) + 1 > limits.max_processes:
                logger.warning(f"Process limit exceeded: {len(children) + 1} > {limits.max_processes}")
                self._kill_process_group(self._process_group_id)
                self._killed = True
                return

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        except Exception as e:
            logger.debug(f"Resource monitoring error: {e}")

    def _collect_resource_usage(self) -> Dict[str, Any]:
        """Collect resource usage stats."""
        usage = {}

        if PSUTIL_AVAILABLE and self._process:
            try:
                proc = psutil.Process(self._process.pid)
                usage["cpu_percent"] = proc.cpu_percent(interval=0.1)
                usage["memory_mb"] = round(proc.memory_info().rss / 1024 / 1024, 2)
                usage["num_threads"] = proc.num_threads()
                usage["num_fds"] = proc.num_fds() if hasattr(proc, "num_fds") else 0

                # Children
                children = proc.children(recursive=True)
                usage["child_processes"] = len(children)

                # Total memory including children
                total_mem = proc.memory_info().rss
                for child in children:
                    try:
                        total_mem += child.memory_info().rss
                    except Exception:
                        pass
                usage["total_memory_mb"] = round(total_mem / 1024 / 1024, 2)

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            except Exception as e:
                usage["error"] = str(e)

        return usage


__all__ = ["SubprocessSandbox"]