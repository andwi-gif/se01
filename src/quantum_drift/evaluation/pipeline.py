"""Offline evaluation pipeline for persisted execution artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quantum_drift.config.loader import load_run_config
from quantum_drift.config.paths import REPO_ROOT
from quantum_drift.evaluation.artifacts import write_evaluation_artifacts
from quantum_drift.evaluation.classification import DriftClassifier
from quantum_drift.evaluation.metrics import build_aggregate_metrics
from quantum_drift.evaluation.taxonomy import load_taxonomy_definition
from quantum_drift.models.evaluation import DriftClassification, RunSummary
from quantum_drift.models.execution import ExecutionResult


@dataclass(frozen=True)
class LoadedEvaluationInputs:
    """Inputs required to evaluate a completed offline execution run."""

    output_dir: Path
    execution_results: tuple[ExecutionResult, ...]
    taxonomy_path: Path


@dataclass(frozen=True)
class EvaluationRun:
    """Structured summary of a completed evaluation run."""

    run_id: str
    output_dir: Path
    summary: RunSummary


def load_evaluation_inputs(
    config_path: Path,
    *,
    repo_root: Path,
    run_id: str | None = None,
    taxonomy_path: Path | None = None,
) -> LoadedEvaluationInputs:
    """Load persisted execution artifacts and the configured taxonomy."""
    config = load_run_config(config_path)
    resolved_run_id = run_id or config.run.name
    output_dir = repo_root / config.output_root / resolved_run_id
    execution_manifest = output_dir / "execution_results.json"
    resolved_taxonomy_path = taxonomy_path or _default_taxonomy_path(repo_root)
    return LoadedEvaluationInputs(
        output_dir=output_dir,
        execution_results=_load_execution_results(execution_manifest),
        taxonomy_path=resolved_taxonomy_path,
    )


def run_evaluation_pipeline(loaded: LoadedEvaluationInputs) -> EvaluationRun:
    """Classify persisted execution results and write summary artifacts."""
    taxonomy = load_taxonomy_definition(loaded.taxonomy_path)
    classifier = DriftClassifier(taxonomy)
    classifications = tuple(classifier.classify(result) for result in loaded.execution_results)
    metrics = build_aggregate_metrics(classifications)
    summary = RunSummary(
        run_id=classifications[0].run_id,
        task_count=len({item.task_id for item in classifications}),
        attempt_count=len(classifications),
        sdk_versions=tuple(sorted({item.sdk_version for item in classifications})),
        modes=tuple(sorted({item.mode for item in classifications})),
        labels=tuple(sorted({item.label for item in classifications})),
        classifications=classifications,
        metrics=metrics,
        classification_counts=_count_labels(classifications),
        artifact_root=str(loaded.output_dir),
    )
    write_evaluation_artifacts(output_dir=loaded.output_dir, summary=summary)
    return EvaluationRun(run_id=summary.run_id, output_dir=loaded.output_dir, summary=summary)


def _load_execution_results(path: Path) -> tuple[ExecutionResult, ...]:
    payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return tuple(ExecutionResult(**result_payload) for result_payload in payload["results"])


def _count_labels(classifications: tuple[DriftClassification, ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for classification in classifications:
        counts[classification.label] = counts.get(classification.label, 0) + 1
    return counts


def _default_taxonomy_path(repo_root: Path) -> Path:
    candidate = repo_root / "configs" / "qiskit_mvp_taxonomy.toml"
    if candidate.exists():
        return candidate
    return REPO_ROOT / "configs" / "qiskit_mvp_taxonomy.toml"
