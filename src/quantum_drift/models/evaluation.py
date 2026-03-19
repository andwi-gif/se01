"""Typed models for drift classification and summary artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class DriftClassification:
    """Drift label derived from a persisted execution result."""

    run_id: str
    task_id: str
    sdk: str
    sdk_version: str
    mode: str
    label: str
    severity: str
    reason: str
    is_recoverable: bool
    execution_status: str
    runtime_name: str
    exit_code: int | None
    timed_out: bool
    exception_type: str | None = None
    exception_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of the artifact."""
        return asdict(self)


@dataclass(frozen=True)
class AggregateMetric:
    """Count/rate aggregate for a classification slice."""

    dimension: str
    value: str
    label: str
    count: int
    total: int
    rate: float

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of the metric row."""
        return asdict(self)


@dataclass(frozen=True)
class RunSummary:
    """Aggregate evaluation summary for one completed run."""

    run_id: str
    task_count: int
    attempt_count: int
    sdk_versions: tuple[str, ...]
    modes: tuple[str, ...]
    labels: tuple[str, ...]
    classifications: tuple[DriftClassification, ...]
    metrics: tuple[AggregateMetric, ...]
    classification_counts: dict[str, int]
    artifact_root: str

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of the artifact."""
        payload = asdict(self)
        payload["classifications"] = [item.to_dict() for item in self.classifications]
        payload["metrics"] = [item.to_dict() for item in self.metrics]
        return payload
