# Task Breakdown

This document breaks the MVP into ordered, PR-sized milestones. Each milestone is intended to be reviewable on its own while still advancing the repository toward a fully runnable offline demo.

## Milestone 1: Skeleton and tooling

### Deliverables
- Create the Python 3.11 package skeleton under `src/quantum_drift/`.
- Add `pyproject.toml` with dependency and tool configuration.
- Configure linting, formatting, type checking, and testing.
- Create baseline directories: `sample_data/`, `artifacts/runs/`, and `tests/`.
- Add initial README setup and development commands.

### Done when
- The package installs in editable mode.
- Lint and test commands run locally and in CI.
- The repository documents how to bootstrap development.

## Milestone 2: Sample dataset, docs, and configs

### Deliverables
- Define schemas for tasks and run configuration.
- Add ten to twenty sample Qiskit pilot tasks under `sample_data/tasks/`.
- Add versioned documentation excerpts for the target SDK versions under `sample_data/docs/`.
- Add sample run configs in YAML or TOML under `sample_data/configs/`.
- Add saved-response or mock backend fixtures so sample runs need no external API key.
- Document the offline sample workflow.

### Done when
- A reviewer can inspect the checked-in sample inputs and understand the MVP benchmark.
- The repository contains a documented no-key path based entirely on `sample_data/`.

## Milestone 3: Generation subsystem

### Deliverables
- Implement typed dataset loaders and validators.
- Implement model backend abstraction with a mock or saved-response backend first.
- Implement vanilla generation mode.
- Implement RAG-docs prompt assembly against local versioned docs.
- Implement rewrite pipeline hooks or baseline rewrite flow.
- Persist `GenerationResult` artifacts for each attempt.
- Add unit tests for task loading, prompt construction, and generation outputs.

### Done when
- A pilot command can produce deterministic generation artifacts from sample inputs.
- All three MVP generation modes are represented in the code path, even if rewrite remains minimal initially.

## Milestone 4: Execution harness

### Deliverables
- Implement execution runner interfaces.
- Add per-version runtime selection for the target Qiskit versions.
- Capture stdout, stderr, exit codes, exceptions, and timing.
- Persist `ExecutionResult` artifacts.
- Add tests for successful execution, expected failures, and timeouts.
- Document how generated code is executed during experiments.

### Done when
- Generated candidates can be executed reproducibly across the target SDK versions.
- Runtime outcomes are stored in structured artifacts rather than ad hoc logs only.

## Milestone 5: Taxonomy and metrics

### Deliverables
- Define the MVP drift taxonomy and classification rules.
- Implement `DriftClassification` generation from execution evidence.
- Implement aggregate metrics by version, mode, and classification label.
- Persist `RunSummary` plus machine-readable metric tables.
- Add tests for classification edge cases and metric aggregation.

### Done when
- A completed run yields both per-attempt drift labels and aggregate summaries.
- The taxonomy is documented well enough for reviewers to interpret results consistently.

## Milestone 6: CLI

### Deliverables
- Add a CLI entrypoint for validation, run execution, evaluation, and summary commands.
- Provide command-line options for selecting sample configs and artifact destinations.
- Print human-readable run summaries.
- Document all supported commands in the README.
- Add CLI integration tests where practical.

### Done when
- A user can launch the offline MVP pilot entirely via CLI.
- The README includes copy-pastable commands for the main workflow.

## Milestone 7: Dashboard

### Deliverables
- Build a local dashboard that reads completed run artifacts from disk.
- Add views for summary metrics, version comparisons, task drill-down, and drift label breakdowns.
- Surface prompt, retrieved context, generated code, and execution evidence for inspection.
- Document dashboard launch and usage.
- Add tests for data loading and any non-trivial view model logic.

### Done when
- A user can inspect completed sample runs visually without rerunning the pipeline.
- Dashboard data is derived from persisted artifacts under `artifacts/runs/`.

## Milestone 8: Final hardening

### Deliverables
- Add CI workflows for lint, tests, and a small end-to-end offline pilot.
- Improve logging, error handling, and reproducibility notes.
- Audit documentation for setup, architecture, commands, and limitations.
- Remove placeholder TODOs from changed production paths.
- Record honest limitations and deferred stretch goals.

### Done when
- CI validates the offline MVP path reliably.
- The repository is documented enough for an external user to run the sample workflow.
- Remaining limitations are explicit, and stretch goals remain out of scope until MVP is green.
