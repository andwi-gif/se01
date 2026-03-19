"""End-to-end offline generation pipeline orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from quantum_drift.config.loader import load_run_config
from quantum_drift.datasets import (
    load_documentation_excerpt_directory,
    load_model_response_fixtures,
    load_tasks,
)
from quantum_drift.generation.artifacts import write_generation_artifacts
from quantum_drift.generation.backends import SavedResponseBackend
from quantum_drift.generation.prompts import PromptBuilder
from quantum_drift.models import (
    DocumentationExcerpt,
    ModelResponseFixture,
    RunConfig,
    Task,
)
from quantum_drift.models.generation import GenerationResult


@dataclass(frozen=True)
class LoadedGenerationInputs:
    """Offline inputs required to run the deterministic generation slice."""

    config: RunConfig
    tasks: tuple[Task, ...]
    docs: tuple[DocumentationExcerpt, ...]
    fixtures: tuple[ModelResponseFixture, ...]


@dataclass(frozen=True)
class GenerationRun:
    """Structured summary of a completed deterministic generation run."""

    run_id: str
    output_dir: Path
    results: tuple[GenerationResult, ...]


def load_generation_inputs(
    config_path: Path, *, repo_root: Path
) -> LoadedGenerationInputs:
    """Load all offline assets referenced by a run config."""
    config = load_run_config(config_path)
    tasks = tuple(load_tasks(repo_root / config.data.task_file))
    docs = tuple(load_documentation_excerpt_directory(repo_root / config.data.docs_path))
    fixtures = tuple(
        load_model_response_fixtures(
            repo_root / config.data.model_response_file,
            task_ids={task.task_id for task in tasks},
            excerpt_ids={excerpt.excerpt_id for excerpt in docs},
        )
    )
    return LoadedGenerationInputs(config=config, tasks=tasks, docs=docs, fixtures=fixtures)


def run_generation_pipeline(
    loaded: LoadedGenerationInputs,
    *,
    repo_root: Path,
    run_id: str | None = None,
) -> GenerationRun:
    """Execute the deterministic offline generation slice and persist artifacts."""
    resolved_run_id = run_id or loaded.config.run.name
    prompt_builder = PromptBuilder()
    backend = SavedResponseBackend(fixtures=loaded.fixtures)
    selected_tasks = loaded.tasks
    if loaded.config.run.max_tasks is not None:
        selected_tasks = selected_tasks[: loaded.config.run.max_tasks]

    results: list[GenerationResult] = []
    baseline_cache: dict[tuple[str, str], str] = {}
    for sdk_version in loaded.config.run.versions:
        for task in selected_tasks:
            if sdk_version not in task.target_versions:
                continue
            for mode in loaded.config.run.modes:
                rewrite_source = None
                if mode == "rewrite":
                    rewrite_source = baseline_cache.get((task.task_id, sdk_version))
                    if rewrite_source is None:
                        msg = (
                            "rewrite mode requires a prior vanilla baseline for "
                            f"task {task.task_id!r} and version {sdk_version!r}"
                        )
                        raise ValueError(msg)
                request = prompt_builder.build_request(
                    run_id=resolved_run_id,
                    task=task,
                    sdk_version=sdk_version,
                    mode=mode,
                    docs=loaded.docs,
                    rewrite_source=rewrite_source,
                )
                result = backend.generate(request)
                results.append(result)
                if mode == "vanilla":
                    baseline_cache[(task.task_id, sdk_version)] = result.generated_code

    output_dir = write_generation_artifacts(
        output_root=repo_root / loaded.config.output_root,
        results=tuple(results),
    )
    return GenerationRun(run_id=resolved_run_id, output_dir=output_dir, results=tuple(results))
