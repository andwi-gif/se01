"""Artifact persistence for execution results."""

from __future__ import annotations

import json
from pathlib import Path

from quantum_drift.models.execution import ExecutionResult


def write_execution_artifacts(*, output_root: Path, results: tuple[ExecutionResult, ...]) -> Path:
    """Persist execution artifacts alongside generation outputs for a run."""
    if not results:
        msg = "results must be non-empty"
        raise ValueError(msg)
    run_id = results[0].run_id
    run_dir = output_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = run_dir / "execution_results.json"
    manifest_payload = {
        "run_id": run_id,
        "result_count": len(results),
        "results": [result.to_dict() for result in results],
    }
    manifest_path.write_text(json.dumps(manifest_payload, indent=2) + "\n", encoding="utf-8")

    for result in results:
        task_dir = run_dir / result.task_id / result.sdk_version / result.mode
        task_dir.mkdir(parents=True, exist_ok=True)
        (task_dir / "execution_result.json").write_text(
            json.dumps(result.to_dict(), indent=2) + "\n",
            encoding="utf-8",
        )
    return run_dir
