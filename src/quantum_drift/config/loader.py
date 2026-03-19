"""Configuration loading for deterministic offline sample runs."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from quantum_drift.models import DataSelection, ExecutionSettings, RunConfig, RunSettings


def _coerce_path(path_str: str) -> Path:
    return Path(path_str)


def load_run_config(path: Path) -> RunConfig:
    """Load a checked-in TOML run config for the offline MVP path."""
    with path.open("rb") as handle:
        payload: dict[str, Any] = tomllib.load(handle)

    run_payload = payload["run"]
    data_payload = payload["data"]
    execution_payload = payload.get("execution")
    execution = None
    if execution_payload is not None:
        execution = ExecutionSettings(
            runtime_manifest=_coerce_path(execution_payload["runtime_manifest"]),
            timeout_seconds=float(execution_payload.get("timeout_seconds", 5.0)),
        )

    return RunConfig(
        schema_version=payload["schema_version"],
        run=RunSettings(
            name=run_payload["name"],
            sdk=run_payload["sdk"],
            versions=tuple(run_payload["versions"]),
            modes=tuple(run_payload["modes"]),
            max_tasks=run_payload.get("max_tasks"),
            notes=run_payload.get("notes"),
        ),
        data=DataSelection(
            task_file=_coerce_path(data_payload["task_file"]),
            docs_path=_coerce_path(data_payload["docs_path"]),
            model_response_file=_coerce_path(data_payload["model_response_file"]),
        ),
        execution=execution,
        output_root=_coerce_path(payload.get("output_root", "artifacts/runs")),
    )
