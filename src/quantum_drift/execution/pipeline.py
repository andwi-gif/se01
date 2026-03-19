"""Execution pipeline for offline generation artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quantum_drift.config.loader import load_run_config
from quantum_drift.execution.artifacts import write_execution_artifacts
from quantum_drift.execution.runner import ExecutionRunner, SubprocessExecutionRunner
from quantum_drift.execution.runtime import RuntimeManifest, load_runtime_manifest
from quantum_drift.models.execution import ExecutionRequest, ExecutionResult
from quantum_drift.models.generation import GenerationResult


@dataclass(frozen=True)
class LoadedExecutionInputs:
    """Inputs required to execute a generated offline run."""

    config_path: Path
    output_root: Path
    generation_results: tuple[GenerationResult, ...]
    runtime_manifest: RuntimeManifest
    timeout_seconds: float


@dataclass(frozen=True)
class ExecutionRun:
    """Structured summary of a completed execution run."""

    run_id: str
    output_dir: Path
    results: tuple[ExecutionResult, ...]


def load_execution_inputs(
    config_path: Path,
    *,
    repo_root: Path,
    run_id: str | None = None,
) -> LoadedExecutionInputs:
    """Load execution inputs from config and persisted generation artifacts."""
    config = load_run_config(config_path)
    resolved_run_id = run_id or config.run.name
    if config.execution is None:
        msg = "Run config must define an [execution] section to execute generated code"
        raise ValueError(msg)
    output_root = repo_root / config.output_root
    generation_manifest = output_root / resolved_run_id / "generation_results.json"
    generation_results = _load_generation_results(generation_manifest)
    runtime_manifest = load_runtime_manifest(
        repo_root / config.execution.runtime_manifest,
        repo_root=repo_root,
    )
    return LoadedExecutionInputs(
        config_path=config_path,
        output_root=output_root,
        generation_results=generation_results,
        runtime_manifest=runtime_manifest,
        timeout_seconds=config.execution.timeout_seconds,
    )


def run_execution_pipeline(
    loaded: LoadedExecutionInputs,
    *,
    runner: ExecutionRunner | None = None,
) -> ExecutionRun:
    """Execute persisted generation results and write execution artifacts."""
    if not loaded.generation_results:
        msg = "generation_results must be non-empty"
        raise ValueError(msg)
    active_runner = runner or SubprocessExecutionRunner()
    results: list[ExecutionResult] = []
    for generated in loaded.generation_results:
        runtime = loaded.runtime_manifest.resolve(generated.sdk_version)
        request = ExecutionRequest(
            run_id=generated.run_id,
            task_id=generated.task_id,
            sdk=generated.sdk,
            sdk_version=generated.sdk_version,
            mode=generated.mode,
            generated_code=generated.generated_code,
        )
        results.append(
            active_runner.run(
                request,
                runtime=runtime,
                timeout_seconds=loaded.timeout_seconds,
            )
        )

    output_dir = write_execution_artifacts(output_root=loaded.output_root, results=tuple(results))
    return ExecutionRun(run_id=results[0].run_id, output_dir=output_dir, results=tuple(results))


def _load_generation_results(path: Path) -> tuple[GenerationResult, ...]:
    payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    results = tuple(GenerationResult(**result_payload) for result_payload in payload["results"])
    return results
