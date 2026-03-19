"""Artifact persistence for offline generation results."""

from __future__ import annotations

import json
from pathlib import Path

from quantum_drift.models.generation import GenerationResult


def write_generation_artifacts(*, output_root: Path, results: tuple[GenerationResult, ...]) -> Path:
    """Persist generation artifacts under a stable run directory layout."""
    if not results:
        msg = "results must be non-empty"
        raise ValueError(msg)
    run_id = results[0].run_id
    run_dir = output_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = run_dir / "generation_results.json"
    manifest_payload = {
        "run_id": run_id,
        "result_count": len(results),
        "results": [result.to_dict() for result in results],
    }
    manifest_path.write_text(json.dumps(manifest_payload, indent=2) + "\n", encoding="utf-8")

    for result in results:
        task_dir = run_dir / result.task_id / result.sdk_version / result.mode
        task_dir.mkdir(parents=True, exist_ok=True)
        (task_dir / "prompt.txt").write_text(result.prompt + "\n", encoding="utf-8")
        (task_dir / "generated_code.py").write_text(result.generated_code, encoding="utf-8")
        (task_dir / "result.json").write_text(
            json.dumps(result.to_dict(), indent=2) + "\n", encoding="utf-8"
        )
    return run_dir
