# se01

This repository is the planning and implementation space for a reproducible Python research artifact and demo app focused on measuring quantum API drift in LLM-generated code across SDK versions.

## Current scaffold

The repository now includes the offline Qiskit MVP through Milestone 5: checked-in sample inputs, deterministic generation, fixture-backed execution, drift taxonomy evaluation, aggregate metrics, and CLI commands for the full offline sample workflow.

### Repository layout

```text
.
├── .github/workflows/ci.yml
├── artifacts/
│   ├── README.md
│   └── runs/
├── configs/
│   └── base.yaml
├── sample_data/
│   ├── configs/
│   │   ├── offline_pilot.toml
│   │   └── offline_smoke.toml
│   ├── docs/
│   │   ├── qiskit_0_45_excerpts.json
│   │   ├── qiskit_1_0_excerpts.json
│   │   ├── qiskit_1_1_excerpts.json
│   │   └── README.md
│   ├── model_responses/
│   │   ├── qiskit_saved_responses.json
│   │   └── README.md
│   └── tasks/
│       ├── qiskit_pilot_tasks.json
│       └── README.md
├── src/
│   └── quantum_drift/
│       ├── cli/
│       ├── config/
│       ├── datasets/
│       ├── evaluation/
│       ├── execution/
│       ├── generation/
│       ├── models/
│       ├── retrieval/
│       ├── rewrite/
│       ├── storage/
│       └── ui/
└── tests/
```

## Getting started

1. Create a Python 3.11 virtual environment.
2. Install the project with development dependencies.
3. Run linting, typing, tests, and the offline sample validation command.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .[dev]
ruff check .
mypy src
pytest
quantum-drift --validate-config sample_data/configs/offline_smoke.toml
quantum-drift --generate-offline sample_data/configs/offline_smoke.toml --run-id readme-smoke
quantum-drift --execute-offline sample_data/configs/offline_smoke.toml --run-id readme-smoke
quantum-drift --evaluate-offline sample_data/configs/offline_smoke.toml --run-id readme-smoke
```

## Offline sample workflow

The repository includes a fully checked-in, no-key sample workflow for the Qiskit-only MVP.

### Included assets

- `sample_data/tasks/qiskit_pilot_tasks.json`: 12 curated Qiskit pilot tasks spanning primitives, transpilation, circuit library usage, observables, control flow, and QASM round-trips.
- `sample_data/docs/qiskit_*_excerpts.json`: versioned local documentation slices for Qiskit `0.45`, `1.0`, and `1.1`.
- `sample_data/configs/offline_pilot.toml`: a full offline pilot config covering all 12 tasks, all 3 target versions, and all 3 MVP generation modes.
- `sample_data/configs/offline_smoke.toml`: a smaller validation config intended for quick local checks.
- `sample_data/model_responses/qiskit_saved_responses.json`: deterministic saved-response fixtures for each pilot task and generation mode.

### Validation command

Use the CLI to validate that the checked-in offline assets are internally consistent:

```bash
quantum-drift --validate-config sample_data/configs/offline_pilot.toml
```

The command loads the TOML run config, task dataset, all versioned documentation excerpts, and the saved-response fixtures, then verifies the cross-references between them.

### Offline generation slice

Milestone 3 now includes a deterministic offline generation slice for the Qiskit MVP. The pipeline loads the checked-in tasks, docs, and saved-response fixtures; constructs prompts for `vanilla`, `rag_docs`, and `rewrite`; and writes structured generation artifacts under `artifacts/runs/<run_id>/`.

### Offline execution slice

Milestone 4 adds a subprocess-based offline execution harness for generated candidates. Execution reads persisted `generation_results.json`, resolves a per-version runtime from `sample_data/configs/qiskit_runtime_manifest.toml`, injects deterministic local Qiskit stub packages from `sample_data/runtime_fixtures/`, and writes structured execution artifacts under the same run directory. This keeps the MVP fully offline and testable even when real Qiskit environments are not installed.

### Offline evaluation slice

Milestone 5 turns persisted execution outcomes into per-attempt drift labels and aggregate metrics. Evaluation reads `execution_results.json`, applies the ordered rules in `configs/qiskit_mvp_taxonomy.toml`, and writes machine-readable summaries back into the same run directory.

#### Copy-pastable smoke workflow

Run the small smoke workflow end to end:

```bash
quantum-drift --generate-offline sample_data/configs/offline_smoke.toml --run-id offline-smoke-demo
quantum-drift --execute-offline sample_data/configs/offline_smoke.toml --run-id offline-smoke-demo
quantum-drift --evaluate-offline sample_data/configs/offline_smoke.toml --run-id offline-smoke-demo
```

The generation step writes:

- `artifacts/runs/offline-smoke-demo/generation_results.json`: manifest of all generated results for the run.
- `artifacts/runs/offline-smoke-demo/<task_id>/<sdk_version>/<mode>/prompt.txt`: the assembled prompt used for that deterministic request.
- `artifacts/runs/offline-smoke-demo/<task_id>/<sdk_version>/<mode>/generated_code.py`: the saved-response output code.
- `artifacts/runs/offline-smoke-demo/<task_id>/<sdk_version>/<mode>/result.json`: the structured `GenerationResult` artifact.

The execution step writes:

- `artifacts/runs/offline-smoke-demo/execution_results.json`: manifest of all execution outcomes for the run.
- `artifacts/runs/offline-smoke-demo/<task_id>/<sdk_version>/<mode>/execution_result.json`: the structured `ExecutionResult` artifact for a single generated candidate.

The evaluation step writes:

- `artifacts/runs/offline-smoke-demo/drift_classifications.json`: manifest of all per-attempt `DriftClassification` records.
- `artifacts/runs/offline-smoke-demo/metrics_by_dimension.json`: aggregate metric rows by `sdk_version` and `mode`.
- `artifacts/runs/offline-smoke-demo/run_summary.json`: top-level `RunSummary` artifact for the completed run.
- `artifacts/runs/offline-smoke-demo/<task_id>/<sdk_version>/<mode>/drift_classification.json`: the per-attempt drift label saved beside the execution artifact.

Each execution artifact captures:

- runtime selection (`qiskit-<version>`)
- stdout and stderr
- process exit code
- timeout status
- parsed exception type/message when Python code fails
- wall-clock duration in seconds

Current limitations for this slice:

- Runtime selection is fixture-backed and deterministic for offline testing; it does not yet create or manage real version-pinned Qiskit virtual environments.
- The harness currently executes one candidate at a time via local subprocesses; parallel scheduling and sandboxing policy controls remain out of scope for this milestone.
#### MVP taxonomy

The current offline taxonomy is intentionally narrow and deterministic. The ordered labels are:

- `no_drift_success`
- `execution_timeout`
- `environment_issue`
- `syntax_or_format_error`
- `module_path_change`
- `missing_symbol`
- `signature_change`
- `semantic_runtime_change`
- `unknown_failure`

The evaluator uses first-match-wins rule ordering from `configs/qiskit_mvp_taxonomy.toml`. In practice:

- successful execution maps to `no_drift_success`
- subprocess timeouts map to `execution_timeout`
- runner failures map to `environment_issue`
- syntax exceptions map to `syntax_or_format_error`
- import-path failures map to `module_path_change`
- missing imports, attributes, or names map to `missing_symbol`
- argument mismatch `TypeError`s map to `signature_change`
- remaining runtime behavior failures fall back to `semantic_runtime_change` or `unknown_failure`

#### Current limitations

- The taxonomy is execution-evidence-only for the offline MVP; it does not yet compare semantic outputs against gold references.
- Aggregate metrics are currently reported by SDK version and generation mode only; task-family breakdowns and dashboard visualizations remain later milestones.
- The only required backend is the checked-in saved-response backend; no live model or API-key flow is included yet.
- `rag_docs` uses deterministic local excerpt selection from `sample_data/docs/`; it does not yet implement embeddings or semantic search.
- `rewrite` remains a minimal baseline path and is not yet wired to iterative failure recovery logic.

## Planning docs

- `docs/ARCHITECTURE.md` outlines the intended single-package Python 3.11 architecture, end-to-end workflow, artifact layout, and core data models.
- `docs/IMPLEMENTATION_PLAN.md` describes the phased MVP delivery plan, including the requirement that the sample workflow remains runnable from checked-in `sample_data/` assets without external API keys.
- `docs/TASK_BREAKDOWN.md` defines the ordered PR-sized milestones and their done conditions.
