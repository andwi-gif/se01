"""Typed models for runtime resolution and execution artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

ExecutionStatus = Literal["success", "runtime_error", "timeout", "runner_error"]


@dataclass(frozen=True)
class ExecutionSettings:
    """Execution settings for an offline run."""

    runtime_manifest: Path
    timeout_seconds: float = 5.0

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0:
            msg = "timeout_seconds must be positive"
            raise ValueError(msg)


@dataclass(frozen=True)
class RuntimeSpec:
    """Resolved runtime metadata for a target SDK version."""

    sdk: str
    sdk_version: str
    python_executable: str
    python_path: tuple[Path, ...] = ()
    environment: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.sdk.strip():
            msg = "sdk must be non-empty"
            raise ValueError(msg)
        if not self.sdk_version.strip():
            msg = "sdk_version must be non-empty"
            raise ValueError(msg)
        if not self.python_executable.strip():
            msg = "python_executable must be non-empty"
            raise ValueError(msg)


@dataclass(frozen=True)
class ExecutionRequest:
    """Executable candidate derived from a generation artifact."""

    run_id: str
    task_id: str
    sdk: str
    sdk_version: str
    mode: str
    generated_code: str

    def __post_init__(self) -> None:
        if not self.generated_code.strip():
            msg = "generated_code must be non-empty"
            raise ValueError(msg)


@dataclass(frozen=True)
class ExecutionResult:
    """Structured execution outcome for one generated candidate."""

    run_id: str
    task_id: str
    sdk: str
    sdk_version: str
    mode: str
    runtime_name: str
    status: ExecutionStatus
    exit_code: int | None
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool
    exception_type: str | None = None
    exception_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of the artifact."""
        return asdict(self)
