# Architecture

## Overview

This repository is planned as a single-package Python 3.11 monorepo for a reproducible research artifact and demo application that measures quantum API drift in LLM-generated code across SDK versions. The MVP intentionally stays narrow:

- Qiskit only.
- Two to three SDK versions under test.
- Ten to twenty pilot tasks.
- Three generation baselines: vanilla prompting, retrieval-augmented prompting over versioned docs, and rewrite-based repair.
- A local CLI and dashboard for running experiments and visualizing drift metrics.

The project should remain runnable from checked-in sample assets, without requiring external API keys. That means every major workflow needs a mock or saved-response path that works from `sample_data/` and produces artifacts under `artifacts/`.

## Repository shape

The codebase should use a standard `src` layout and keep the MVP inside a single Python package.

```text
.
├── docs/
│   ├── ARCHITECTURE.md
│   ├── IMPLEMENTATION_PLAN.md
│   └── TASK_BREAKDOWN.md
├── sample_data/
│   ├── tasks/
│   ├── docs/
│   ├── configs/
│   └── model_responses/
├── artifacts/
│   └── runs/
├── src/
│   └── quantum_drift/
│       ├── __init__.py
│       ├── datasets/
│       ├── generation/
│       ├── retrieval/
│       ├── rewrite/
│       ├── execution/
│       ├── evaluation/
│       ├── ui/
│       ├── cli/
│       ├── config/
│       └── models/
├── tests/
└── README.md
```

A single-package design keeps packaging, typing, test setup, and artifact management simple while still allowing the code to be modular by domain.

## `src/quantum_drift/` module layout

### `quantum_drift.datasets`
Responsible for loading, validating, and normalizing benchmark tasks and any version metadata.

Expected responsibilities:
- Read task definitions from YAML, JSON, or TOML backed assets in `sample_data/tasks/`.
- Resolve SDK version targets and prompt templates.
- Provide deterministic task iteration for reproducible runs.

Representative contents:
- `loader.py`
- `validators.py`
- `registry.py`

### `quantum_drift.generation`
Responsible for invoking model backends and producing candidate code generations.

Expected responsibilities:
- Support generation modes: vanilla, RAG-docs, and rewrite baseline orchestration.
- Abstract model providers behind a common interface.
- Include a mock or saved-response backend for keyless local execution.

Representative contents:
- `backends.py`
- `prompts.py`
- `pipeline.py`

### `quantum_drift.retrieval`
Responsible for indexing and retrieving version-specific documentation passages.

Expected responsibilities:
- Build lightweight local retrieval indices from checked-in docs slices.
- Retrieve passages keyed by SDK name and version.
- Expose deterministic retrieval for experiments.

Representative contents:
- `index.py`
- `retriever.py`
- `corpus.py`

### `quantum_drift.rewrite`
Responsible for repair or migration passes applied after an initial generation.

Expected responsibilities:
- Convert failed or drifted code into a revised candidate.
- Track rewrite provenance and rationale.
- Support fixed heuristics and model-assisted rewriting, while preserving a sample-data path.

Representative contents:
- `rewriter.py`
- `rules.py`
- `pipeline.py`

### `quantum_drift.execution`
Responsible for running generated code safely against targeted SDK versions.

Expected responsibilities:
- Materialize isolated execution environments or adapters per SDK version.
- Execute generated programs with timeouts and structured capture of stdout, stderr, and exceptions.
- Normalize runtime outcomes for downstream evaluation.

Representative contents:
- `runner.py`
- `sandbox.py`
- `environments.py`

### `quantum_drift.evaluation`
Responsible for drift labeling, metrics, aggregation, and summary reporting.

Expected responsibilities:
- Classify failures into a drift taxonomy.
- Compute success, compatibility, and repair metrics across versions and strategies.
- Produce run summaries and machine-readable outputs.

Representative contents:
- `classification.py`
- `metrics.py`
- `summary.py`

### `quantum_drift.ui`
Responsible for the local dashboard and supporting view models.

Expected responsibilities:
- Load run artifacts from disk.
- Visualize outcomes by task, version, generation mode, and classification.
- Provide drill-down into prompts, retrieved docs, code, and execution traces.

Representative contents:
- `dashboard.py`
- `views.py`
- `data_source.py`

### `quantum_drift.cli`
Responsible for user-facing commands that tie the system together.

Expected responsibilities:
- Run pilots from sample configs.
- Validate datasets and configs.
- Build retrieval indices.
- Summarize or inspect completed runs.

Representative contents:
- `main.py`
- `commands/run.py`
- `commands/evaluate.py`
- `commands/dashboard.py`

### Supporting modules

#### `quantum_drift.config`
- Typed config loading from YAML or TOML.
- Default sample configs.
- Environment-independent path resolution.

#### `quantum_drift.models`
- Shared typed data models used across all subsystems.
- Serialization helpers for artifact persistence.

## End-to-end workflow

The expected MVP workflow runs from deterministic local inputs through persisted experiment outputs and dashboard views.

1. **Task loading**
   - The CLI selects a run config from `sample_data/configs/`.
   - Dataset loaders read task records from `sample_data/tasks/`.
   - Validation ensures each task has a stable identifier, prompt text, expected target SDK/version metadata, and evaluation hints.

2. **Generation strategy setup**
   - The run config selects one or more modes: vanilla, RAG-docs, or rewrite.
   - The generation subsystem resolves the model backend.
   - For offline MVP runs, the backend can be a mock or saved-response provider from `sample_data/model_responses/`.

3. **Retrieval augmentation when enabled**
   - If RAG-docs is active, the retrieval subsystem loads the versioned document index from `sample_data/docs/`.
   - Relevant passages for the requested SDK version are fetched and attached to the prompt context.
   - Retrieved passages are recorded in the generation artifacts for auditability.

4. **Initial code generation**
   - The generation pipeline builds a structured prompt from the task, selected SDK version, optional retrieved context, and run settings.
   - The model backend produces code and metadata such as prompt hash, backend name, latency, and token usage if available.
   - The system writes a `GenerationResult` artifact for each task/version/mode attempt.

5. **Execution harness**
   - The execution subsystem selects the target SDK runtime for each version under test.
   - Generated code runs inside a controlled harness with timeout and error capture.
   - The harness emits an `ExecutionResult` with status, logs, and normalized exception data.

6. **Rewrite path when configured**
   - If rewrite mode is enabled, failed outputs or drift-labeled outputs can be passed to the rewrite subsystem.
   - The rewrite subsystem creates an updated candidate and records lineage back to the original generation.
   - The revised candidate is re-executed and persisted as a separate attempt.

7. **Classification and metrics**
   - The evaluation subsystem classifies each execution outcome into the drift taxonomy.
   - Aggregate metrics are computed per SDK version, task family, and generation mode.
   - The run is summarized into a `RunSummary` that contains headline metrics and artifact pointers.

8. **Artifact persistence**
   - Every major step persists structured records beneath `artifacts/runs/<run_id>/`.
   - Artifacts are designed to be inspectable, reproducible, and reloadable without rerunning the experiment.

9. **Dashboard visualization**
   - The dashboard reads one or more completed runs from disk.
   - Users can compare success rates, drift classifications, and rewrite recovery by version and mode.
   - Drill-down pages expose the task prompt, retrieved docs, generated code, execution traces, and classifications.

## Artifact storage layout under `artifacts/runs/`

The current MVP writes one directory per run under `artifacts/runs/<run_id>/`. The layout below reflects the checked-in offline workflow that the CLI and CI smoke path actually exercise today.

```text
artifacts/
└── runs/
    └── <run_id>/
        ├── generation_results.json
        ├── execution_results.json
        ├── drift_classifications.json
        ├── metrics_by_dimension.json
        ├── run_summary.json
        └── <task_id>/
            └── <sdk_version>/
                └── <mode>/
                    ├── prompt.txt
                    ├── generated_code.py
                    ├── result.json
                    ├── execution_result.json
                    └── drift_classification.json
```

Current conventions:
- `run_id` comes from the run config name unless the CLI overrides it with `--run-id`.
- Run-level manifests (`generation_results.json`, `execution_results.json`, `drift_classifications.json`, `metrics_by_dimension.json`, and `run_summary.json`) are the stable entry points for CLI summaries and dashboard loading.
- Per-attempt leaf files keep prompt/code/evidence together under `<task_id>/<sdk_version>/<mode>/` for easy drill-down.
- The MVP does not yet write a dedicated pipeline log, cached dashboard tables, or a copied run-config manifest into each run directory.

## Core data models

These models should be implemented as typed public APIs, likely with dataclasses or Pydantic models, and serialized to JSON for artifact persistence.

### `Task`
Represents one benchmark unit to be attempted across one or more SDK versions.

Suggested fields:
- `task_id: str`
- `title: str`
- `description: str`
- `prompt: str`
- `sdk: str`
- `target_versions: list[str]`
- `tags: list[str]`
- `expected_signals: dict[str, str] | None`
- `metadata: dict[str, str | int | float | bool]`

Purpose:
- Provides the canonical prompt and evaluation metadata.
- Anchors lineage across generation, execution, and classification outputs.

### `GenerationResult`
Represents one generated code attempt for a task under a specific mode and SDK version.

Suggested fields:
- `run_id: str`
- `task_id: str`
- `sdk: str`
- `sdk_version: str`
- `mode: str`
- `attempt_index: int`
- `backend_name: str`
- `prompt_text: str`
- `retrieved_context_ids: list[str]`
- `generated_code: str`
- `latency_ms: int | None`
- `token_usage: dict[str, int] | None`
- `parent_attempt_id: str | None`
- `created_at: str`

Purpose:
- Captures exact prompting context and produced code.
- Supports reproducibility, auditing, and rewrite lineage.

### `ExecutionResult`
Represents the structured outcome of running one generated candidate.

Suggested fields:
- `run_id: str`
- `task_id: str`
- `sdk: str`
- `sdk_version: str`
- `mode: str`
- `attempt_index: int`
- `status: str`
- `exit_code: int | None`
- `stdout: str`
- `stderr: str`
- `exception_type: str | None`
- `exception_message: str | None`
- `duration_ms: int`
- `environment_ref: str`
- `artifacts: dict[str, str]`

Purpose:
- Normalizes runtime evidence for downstream classification.
- Separates execution semantics from raw process details.

### `DriftClassification`
Represents the evaluator's interpretation of whether and how API drift occurred.

Suggested fields:
- `run_id: str`
- `task_id: str`
- `sdk: str`
- `sdk_version: str`
- `mode: str`
- `attempt_index: int`
- `label: str`
- `severity: str`
- `confidence: float`
- `reason: str`
- `evidence_refs: list[str]`
- `is_recoverable: bool`

Representative labels for the MVP taxonomy:
- `no_drift_success`
- `execution_timeout`
- `environment_issue`
- `syntax_or_format_error`
- `module_path_change`
- `missing_symbol`
- `signature_change`
- `semantic_runtime_change`
- `unknown_failure`

Purpose:
- Provides interpretable failure categories for metrics and analysis.
- Enables reporting on which strategies are best at mitigating specific drift types.

### `RunSummary`
Represents an aggregate view of a completed run.

Suggested fields:
- `run_id: str`
- `config_ref: str`
- `started_at: str`
- `completed_at: str`
- `task_count: int`
- `attempt_count: int`
- `modes: list[str]`
- `sdk_versions: list[str]`
- `success_rate_by_mode: dict[str, float]`
- `success_rate_by_version: dict[str, float]`
- `drift_rate_by_label: dict[str, float]`
- `rewrite_recovery_rate: float | None`
- `artifact_root: str`

Purpose:
- Supports quick CLI summaries and dashboard loading.
- Acts as the stable top-level record for comparisons across runs.

## Design principles

- **Reproducibility first**: every MVP feature must work from checked-in sample assets and deterministic configs.
- **Traceable artifacts**: prompts, retrieved context, code, logs, and classifications all need stable on-disk records.
- **Version awareness**: the SDK version is a first-class dimension across datasets, retrieval, execution, and reporting.
- **Single-package simplicity**: keep orchestration inside one Python package until the MVP is complete and validated.
- **Offline-friendly demos**: no external API key should be required to run the sample workflow.
