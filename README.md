# se01

This repository is the planning and implementation space for a reproducible Python research artifact and demo app focused on measuring quantum API drift in LLM-generated code across SDK versions.

## Current implementation status

The repository now includes the offline Qiskit MVP through the Milestone 8 hardening scope: checked-in sample inputs, deterministic generation, fixture-backed execution, drift taxonomy evaluation, aggregate metrics, CLI commands for the full offline sample workflow, a minimal local dashboard for inspecting saved run artifacts, and CI coverage for Ruff, mypy, pytest, plus the checked-in offline smoke workflow.

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
3. Run linting, typing, tests, and the checked-in offline smoke workflow.

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
quantum-drift --summary-run readme-smoke
```

Those five CLI commands are the same offline MVP path that CI now validates on every push and pull request, using only checked-in `sample_data/` assets and writing artifacts under `artifacts/runs/<run_id>/`.

If one of the offline stages is missing its prerequisite artifacts, the CLI now exits with a short user-facing error instead of a Python traceback. For example, `--execute-offline` explains when `generation_results.json` is missing for the requested run id, and `--evaluate-offline` does the same for `execution_results.json`.

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
quantum-drift --validate-config sample_data/configs/offline_smoke.toml
quantum-drift --generate-offline sample_data/configs/offline_smoke.toml --run-id offline-smoke-demo
quantum-drift --execute-offline sample_data/configs/offline_smoke.toml --run-id offline-smoke-demo
quantum-drift --evaluate-offline sample_data/configs/offline_smoke.toml --run-id offline-smoke-demo
quantum-drift --summary-run offline-smoke-demo
```

This sequence is intentionally reproducible:

- `sample_data/configs/offline_smoke.toml` limits the run to one SDK version (`1.0`), two generation modes (`vanilla` and `rag_docs`), and three checked-in pilot tasks.
- Generation uses only `sample_data/model_responses/qiskit_saved_responses.json`; no API key or hosted model call is required.
- Execution uses the checked-in runtime fixture manifest and local stub packages, so the smoke run does not depend on a system Qiskit installation.
- Evaluation reads the saved execution evidence and applies the checked-in taxonomy rules without recomputing generations.
- The summary command proves that a completed run can be inspected from persisted artifacts alone.

For a successful smoke run, expect the following run-level artifacts under `artifacts/runs/offline-smoke-demo/`:

- `generation_results.json`
- `execution_results.json`
- `drift_classifications.json`
- `metrics_by_dimension.json`
- `run_summary.json`

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

### Offline summary command

Milestone 6 also requires a dedicated summary command that reads the saved evaluation artifacts without rerunning generation, execution, or evaluation. Use `--summary-run` with either a run id under `artifacts/runs/` or an explicit run directory path:

```bash
quantum-drift --summary-run offline-smoke-demo
quantum-drift --summary-run artifacts/runs/offline-smoke-demo
```

The summary output prints:

- run id
- task count
- attempt count
- SDK versions
- generation modes
- drift label counts
- aggregate metrics grouped by saved dimension values

### CI reproducibility contract

The GitHub Actions workflow in `.github/workflows/ci.yml` now enforces the Milestone 8 offline MVP contract by running:

- `ruff check .`
- `mypy src`
- `pytest`
- the full checked-in offline smoke workflow:
  - `quantum-drift --validate-config sample_data/configs/offline_smoke.toml`
  - `quantum-drift --generate-offline sample_data/configs/offline_smoke.toml --run-id <ci-run-id>`
  - `quantum-drift --execute-offline sample_data/configs/offline_smoke.toml --run-id <ci-run-id>`
  - `quantum-drift --evaluate-offline sample_data/configs/offline_smoke.toml --run-id <ci-run-id>`
  - `quantum-drift --summary-run <ci-run-id>`

After the CLI steps finish, CI also checks that the expected run directory exists and that the smoke run produced both:

- run-level manifests (`generation_results.json`, `execution_results.json`, `drift_classifications.json`, `metrics_by_dimension.json`, and `run_summary.json`)
- per-attempt leaf artifacts for at least one generated candidate (`prompt.txt`, `generated_code.py`, `result.json`, `execution_result.json`, and `drift_classification.json`)

### Local dashboard

Milestone 7 now includes a lightweight local dashboard implemented with Python standard-library WSGI tooling, so the MVP stays fully offline and adds no hosted-service dependency. The dashboard reads existing files from `artifacts/runs/<run_id>/`; it does not recompute metrics.

Launch the dashboard after generating, executing, and evaluating a run:

```bash
quantum-drift --dashboard-run artifacts/runs/offline-smoke-demo
```

Useful options:

```bash
quantum-drift --dashboard-run artifacts/runs/offline-smoke-demo --dashboard-host 127.0.0.1 --dashboard-port 8000
quantum-drift --dashboard-run artifacts/runs/offline-smoke-demo --dashboard-port 0
```

Then open the printed `Dashboard URL` in a browser. The page currently shows:

- run-level summary counts and label totals
- grouped metrics by SDK version and generation mode
- a selectable task/version/mode drill-down list
- saved prompt text, generated code, execution stdout/stderr, exception evidence, and classification metadata for the selected record

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
- CI proves the checked-in offline smoke path only; the larger `offline_pilot.toml` configuration remains a local/manual run because it is intentionally broader and slower than the required smoke gate.
- The smoke run uses fixture-backed runtime packages instead of real version-pinned Qiskit installations, which keeps the MVP deterministic but means CI is validating the offline harness contract rather than upstream wheel compatibility.

## Planning docs

- `docs/ARCHITECTURE.md` outlines the intended single-package Python 3.11 architecture, end-to-end workflow, artifact layout, and core data models.
- `docs/IMPLEMENTATION_PLAN.md` describes the phased MVP delivery plan, including the requirement that the sample workflow remains runnable from checked-in `sample_data/` assets without external API keys. Its final hardening phase corresponds to the Milestone 8 documentation/CI polish now reflected in this README.
- `docs/TASK_BREAKDOWN.md` defines the ordered PR-sized milestones and their done conditions, including the Milestone 8 hardening checklist for CI, documentation, and honest limitations.
