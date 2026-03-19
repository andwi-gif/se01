# Implementation Plan

## Goal

Deliver the MVP for measuring quantum API drift in LLM-generated code across Qiskit SDK versions as a reproducible Python 3.11 artifact and demo app. The work should stay focused on the agreed MVP:

- Qiskit only.
- Two to three SDK versions.
- Ten to twenty pilot tasks.
- Vanilla, RAG-docs, and rewrite baselines.
- Metrics dashboard, CLI, tests, and CI.

A non-negotiable MVP requirement is that the system remains runnable from checked-in `sample_data/` assets without external API keys. Any hosted model provider integration must therefore be optional and secondary to a mock or saved-response backend.

## Delivery principles

- Build the smallest end-to-end slice first, then deepen coverage.
- Prefer deterministic local assets over network dependencies.
- Keep configuration in YAML or TOML so experiments are reproducible.
- Add tests alongside each non-trivial subsystem.
- Update documentation and runnable commands as behavior becomes available.

## Phase 1: Repository bootstrap

### Objectives
Establish the Python 3.11 project skeleton, packaging, tooling, and baseline development workflow.

### Scope
- Create `src/quantum_drift/` with the expected top-level modules.
- Add project metadata and dependency management for Python 3.11.
- Configure linting, formatting, type checking, and testing.
- Add initial artifact, sample data, and test directory structure.

### Outputs
- `pyproject.toml` with project metadata and tooling configuration.
- Package skeleton under `src/quantum_drift/`.
- `tests/` initialized with smoke coverage.
- `sample_data/` and `artifacts/runs/` directories created.
- README updated with setup and basic commands.

### Exit criteria
- A developer can create an environment, install the package, and run lint/tests locally.
- CI can execute the baseline quality gates.

## Phase 2: Sample dataset and configs

### Objectives
Create the minimal reproducible inputs needed to exercise the full MVP offline.

### Scope
- Define task schemas and sample Qiskit pilot tasks.
- Check in versioned documentation excerpts for retrieval experiments.
- Add sample YAML or TOML configs for pilot runs.
- Add mock or saved-response model outputs for deterministic generation.

### Outputs
- `sample_data/tasks/` with ten to twenty curated pilot tasks.
- `sample_data/docs/` with version-scoped Qiskit documentation slices.
- `sample_data/configs/` with pilot run definitions.
- `sample_data/model_responses/` or equivalent offline backend fixtures.

### Exit criteria
- The repository contains enough checked-in data to run at least one meaningful offline pilot.
- No external API key is required for the sample run path.

## Phase 3: Generation modes

### Objectives
Implement the candidate code generation subsystem and the three MVP baselines.

### Scope
- Implement typed task loading and prompt construction.
- Add a backend abstraction for model providers.
- Implement offline mock/saved-response backend first.
- Add vanilla generation mode.
- Add retrieval-augmented prompt assembly using local docs.
- Add rewrite orchestration hooks for post-failure repair.

### Outputs
- Generation pipeline with structured `GenerationResult` persistence.
- Retrieval integration for version-aware context attachment.
- Baseline prompt templates and mode selection.
- Unit tests covering prompt assembly, backend selection, and offline generation.

### Exit criteria
- A configured pilot run can produce stored generations in each MVP mode.
- Offline sample execution remains fully supported.

## Phase 4: Execution harness

### Objectives
Run generated code against targeted Qiskit versions and capture structured outcomes.

### Scope
- Implement execution adapters or isolated environments per SDK version.
- Add timeout, stdout/stderr capture, and exception normalization.
- Persist `ExecutionResult` artifacts per task/version/mode.
- Ensure the harness can be exercised in tests without paid services.

### Outputs
- Execution runner APIs.
- Runtime environment resolution logic.
- Structured logs and execution artifacts.
- Tests covering success, failure, and timeout scenarios.

### Exit criteria
- Generated candidates can be executed reproducibly for two to three target versions.
- Failures are captured in structured data rather than only raw logs.

## Phase 5: Classification and metrics

### Objectives
Turn raw execution outcomes into interpretable drift categories and reportable metrics.

### Scope
- Define the MVP drift taxonomy.
- Implement deterministic classification rules over execution evidence.
- Compute summary metrics by mode, version, task family, and drift label.
- Persist `DriftClassification` and `RunSummary` artifacts.

### Outputs
- Classification engine and taxonomy definitions.
- Metric aggregation utilities and export tables.
- CLI-friendly summary output.
- Tests for rule behavior and aggregate calculations.

### Exit criteria
- Completed runs produce both detailed labels and aggregate metrics.
- Summary artifacts are sufficient for dashboard loading without recomputation.

## Phase 6: CLI and dashboard

### Objectives
Provide a usable local interface for running pilots and inspecting results.

### Scope
- Implement CLI commands for validation, running pilots, evaluation, and dashboard launch.
- Build a lightweight dashboard that reads saved run artifacts.
- Add views for run summaries, drill-down by task, and drift breakdowns.
- Document all user-facing commands.

### Outputs
- `quantum-drift` CLI entrypoint.
- Local dashboard application.
- README sections for setup, pilot execution, and dashboard usage.
- Optional sample screenshots once UI exists.

### Exit criteria
- A user can run an offline pilot from `sample_data/` and inspect results through both CLI and dashboard.
- Dashboard data loading relies on saved artifacts, not live recomputation only.

## Phase 7: CI hardening and polish

### Objectives
Make the MVP robust, repeatable, and ready for external use.

### Scope
- Add or refine CI workflows for lint, tests, and sample pilot execution.
- Validate packaging and reproducibility assumptions.
- Improve logging, error messages, and documentation.
- Identify remaining limitations clearly and defer stretch work until MVP is green.

### Outputs
- CI workflow that runs lint, tests, and a small end-to-end sample pilot.
- Hardened test fixtures for deterministic runs.
- Finalized docs on architecture, implementation, and usage.

### Exit criteria
- CI passes consistently on the offline MVP path.
- The repository can be cloned and exercised without paid credentials.
- Remaining limitations are documented honestly.

## Cross-cutting requirements

The following requirements apply to every phase, not just the final one:

- **Runnable from `sample_data/`**: the MVP must always preserve a documented no-key demo path.
- **Typed public APIs**: all public interfaces should include type hints.
- **Artifact traceability**: run outputs should land under `artifacts/` with stable structure.
- **Tests for non-trivial behavior**: each subsystem should ship with focused coverage.
- **Documentation freshness**: README and docs must be updated when commands or behavior change.

## Suggested implementation order

1. Bootstrap package/tooling.
2. Define data models and sample schemas.
3. Add offline sample dataset, configs, and saved model responses.
4. Implement vanilla generation end-to-end.
5. Add retrieval and RAG-docs mode.
6. Add execution harness across target versions.
7. Add drift classification and metrics.
8. Add rewrite baseline.
9. Add CLI ergonomics and dashboard.
10. Harden CI and documentation.

This ordering prioritizes the earliest possible end-to-end offline pilot while still reaching the full MVP feature set.
