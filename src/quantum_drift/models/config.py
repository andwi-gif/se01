"""Typed configuration models for offline quantum drift sample runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from quantum_drift.models.execution import ExecutionSettings


@dataclass(frozen=True)
class DataSelection:
    """Sample-data inputs selected for a run."""

    task_file: Path
    docs_path: Path
    model_response_file: Path


@dataclass(frozen=True)
class RunSettings:
    """Top-level run settings for a deterministic pilot."""

    name: str
    sdk: str
    versions: tuple[str, ...]
    modes: tuple[str, ...]
    max_tasks: int | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            msg = "RunSettings.name must be non-empty"
            raise ValueError(msg)
        if self.sdk != "qiskit":
            msg = "Milestone 2 configs must target the qiskit SDK"
            raise ValueError(msg)
        if not self.versions:
            msg = "RunSettings.versions must contain at least one version"
            raise ValueError(msg)
        if not self.modes:
            msg = "RunSettings.modes must contain at least one generation mode"
            raise ValueError(msg)


@dataclass(frozen=True)
class RunConfig:
    """Deterministic offline pilot configuration loaded from TOML."""

    schema_version: str
    run: RunSettings
    data: DataSelection
    execution: ExecutionSettings | None = None
    output_root: Path = field(default_factory=lambda: Path("artifacts/runs"))

    def __post_init__(self) -> None:
        if not self.schema_version.strip():
            msg = "schema_version must be non-empty"
            raise ValueError(msg)
