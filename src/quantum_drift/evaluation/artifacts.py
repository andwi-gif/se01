"""Artifact persistence for evaluation outputs."""

from __future__ import annotations

import json
from pathlib import Path

from quantum_drift.models.evaluation import RunSummary


def write_evaluation_artifacts(*, output_dir: Path, summary: RunSummary) -> Path:
    """Persist per-attempt classifications and aggregate summary artifacts."""
    manifest_path = output_dir / "drift_classifications.json"
    manifest_payload = {
        "run_id": summary.run_id,
        "classification_count": len(summary.classifications),
        "classifications": [item.to_dict() for item in summary.classifications],
    }
    manifest_path.write_text(json.dumps(manifest_payload, indent=2) + "\n", encoding="utf-8")

    metrics_path = output_dir / "metrics_by_dimension.json"
    metrics_payload = {
        "run_id": summary.run_id,
        "metric_count": len(summary.metrics),
        "metrics": [item.to_dict() for item in summary.metrics],
    }
    metrics_path.write_text(json.dumps(metrics_payload, indent=2) + "\n", encoding="utf-8")

    summary_path = output_dir / "run_summary.json"
    summary_path.write_text(json.dumps(summary.to_dict(), indent=2) + "\n", encoding="utf-8")

    for classification in summary.classifications:
        task_dir = (
            output_dir
            / classification.task_id
            / classification.sdk_version
            / classification.mode
        )
        task_dir.mkdir(parents=True, exist_ok=True)
        (task_dir / "drift_classification.json").write_text(
            json.dumps(classification.to_dict(), indent=2) + "\n",
            encoding="utf-8",
        )
    return output_dir
