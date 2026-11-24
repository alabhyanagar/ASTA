"""
ASTA Worker Package
"""

from .sandbox import (
    SandboxBackend,
    ResourceLimits,
    NetworkPolicy,
    MountSpec,
    ExecutionRequest,
    ExecutionResult,
    BaseSandbox,
    SandboxFactory,
)

try:
    from .docker_sandbox import DockerSandbox
except ImportError:
    DockerSandbox = None

try:
    from .subprocess_sandbox import SubprocessSandbox
except ImportError:
    SubprocessSandbox = None

__all__ = [
    "SandboxBackend",
    "ResourceLimits",
    "NetworkPolicy",
    "MountSpec",
    "ExecutionRequest",
    "ExecutionResult",
    "BaseSandbox",
    "SandboxFactory",
]

if DockerSandbox:
    __all__.append("DockerSandbox")
if SubprocessSandbox:
    __all__.append("SubprocessSandbox")