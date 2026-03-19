"""Helpers for rendering persisted offline run summaries."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SummaryMetricRow:
    """One aggregate metric row loaded from disk."""

    dimension: str
    value: str
    label: str
    count: int
    total: int
    rate: float


@dataclass(frozen=True)
class PersistedRunSummary:
    """Run summary data read from persisted evaluation artifacts."""

    run_dir: Path
    run_id: str
    task_count: int
    attempt_count: int
    sdk_versions: tuple[str, ...]
    modes: tuple[str, ...]
    classification_counts: dict[str, int]
    metrics: tuple[SummaryMetricRow, ...]


def resolve_run_directory(run_reference: str, *, repo_root: Path) -> Path:
    """Resolve a CLI run reference to a completed run directory."""
    candidate = Path(run_reference)
    if candidate.exists():
        return candidate.resolve()
    return (repo_root / "artifacts" / "runs" / run_reference).resolve()


def load_persisted_run_summary(run_dir: Path) -> PersistedRunSummary:
    """Load the saved summary and metrics artifacts for a completed run."""
    summary_payload = _read_json(run_dir / "run_summary.json")
    metrics_payload = _read_json(run_dir / "metrics_by_dimension.json")
    metrics = tuple(
        SummaryMetricRow(
            dimension=str(item["dimension"]),
            value=str(item["value"]),
            label=str(item["label"]),
            count=int(item["count"]),
            total=int(item["total"]),
            rate=float(item["rate"]),
        )
        for item in metrics_payload["metrics"]
    )
    return PersistedRunSummary(
        run_dir=run_dir,
        run_id=str(summary_payload["run_id"]),
        task_count=int(summary_payload["task_count"]),
        attempt_count=int(summary_payload["attempt_count"]),
        sdk_versions=tuple(str(item) for item in summary_payload["sdk_versions"]),
        modes=tuple(str(item) for item in summary_payload["modes"]),
        classification_counts={
            str(label): int(count)
            for label, count in dict(summary_payload["classification_counts"]).items()
        },
        metrics=metrics,
    )


def format_run_summary(summary: PersistedRunSummary) -> str:
    """Render a readable persisted run summary for CLI output."""
    lines = [
        f"Summary run directory: {summary.run_dir}",
        f"Run ID: {summary.run_id}",
        f"Task count: {summary.task_count}",
        f"Attempt count: {summary.attempt_count}",
        f"SDK versions: {', '.join(summary.sdk_versions) if summary.sdk_versions else '(none)'}",
        f"Generation modes: {', '.join(summary.modes) if summary.modes else '(none)'}",
        "Drift label counts:",
    ]
    if summary.classification_counts:
        for label, count in sorted(summary.classification_counts.items()):
            lines.append(f"  - {label}: {count}")
    else:
        lines.append("  - (none)")

    lines.append("Aggregate metrics by dimension:")
    for dimension, rows in _group_metrics(summary.metrics).items():
        lines.append(f"  {dimension}:")
        for row in rows:
            percentage = row.rate * 100
            lines.append(
                "    - "
                f"{row.value} | {row.label} | count={row.count}/{row.total} "
                f"({percentage:.1f}%)"
            )

    return "\n".join(lines)


def _group_metrics(
    metrics: tuple[SummaryMetricRow, ...],
) -> dict[str, tuple[SummaryMetricRow, ...]]:
    grouped: defaultdict[str, list[SummaryMetricRow]] = defaultdict(list)
    for metric in metrics:
        grouped[metric.dimension].append(metric)
    return {
        dimension: tuple(
            sorted(rows, key=lambda row: (row.value, row.label))
        )
        for dimension, rows in sorted(grouped.items())
    }


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        msg = f"Expected a JSON object in {path}."
        raise ValueError(msg)
    return payload
