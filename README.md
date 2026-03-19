# se01

This repository is the planning and implementation space for a reproducible Python research artifact and demo app focused on measuring quantum API drift in LLM-generated code across SDK versions.

## Current scaffold

The repository now includes the Milestone 2 offline inputs for the Qiskit-only MVP: typed task/config models, validated sample datasets, versioned documentation excerpts, deterministic saved model responses, and CLI validation for the no-key sample workflow.

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
```

## Offline sample workflow

The repository now includes a fully checked-in, no-key sample input set for Milestone 2.

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

Run the small smoke workflow locally with checked-in sample data only:

```bash
quantum-drift --generate-offline sample_data/configs/offline_smoke.toml --run-id offline-smoke-demo
```

This command writes:

- `artifacts/runs/offline-smoke-demo/generation_results.json`: manifest of all generated results for the run.
- `artifacts/runs/offline-smoke-demo/<task_id>/<sdk_version>/<mode>/prompt.txt`: the assembled prompt used for that deterministic request.
- `artifacts/runs/offline-smoke-demo/<task_id>/<sdk_version>/<mode>/generated_code.py`: the saved-response output code.
- `artifacts/runs/offline-smoke-demo/<task_id>/<sdk_version>/<mode>/result.json`: the structured `GenerationResult` artifact.

Current limitations for this slice:

- The only required backend is the checked-in saved-response backend; no live model or API-key flow is included yet.
- `rag_docs` uses deterministic local excerpt selection from `sample_data/docs/`; it does not yet implement embeddings or semantic search.
- `rewrite` is represented as an orchestration hook that rewrites from the vanilla baseline prompt path, but execution, drift classification, metrics, and dashboard features remain out of scope for this PR.

## Planning docs

- `docs/ARCHITECTURE.md` outlines the intended single-package Python 3.11 architecture, end-to-end workflow, artifact layout, and core data models.
- `docs/IMPLEMENTATION_PLAN.md` describes the phased MVP delivery plan, including the requirement that the sample workflow remains runnable from checked-in `sample_data/` assets without external API keys.
- `docs/TASK_BREAKDOWN.md` defines the ordered PR-sized milestones and their done conditions.
