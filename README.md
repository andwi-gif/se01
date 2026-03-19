# se01

This repository is the planning and implementation space for a reproducible Python research artifact and demo app focused on measuring quantum API drift in LLM-generated code across SDK versions.

## Current scaffold

The repository now includes an initial Python 3.11 `src`-layout package scaffold for `quantum_drift`, along with baseline configuration, sample-data, artifact, and test directories. The scaffold is intentionally minimal so later PRs can layer in the MVP subsystems without needing to revisit packaging or CI setup.

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
│   │   └── pilot.yaml
│   ├── docs/
│   │   └── README.md
│   ├── model_responses/
│   │   └── README.md
│   └── tasks/
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
3. Run linting, typing, tests, and the scaffold CLI smoke check.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .[dev]
ruff check .
mypy src
pytest
quantum-drift --ensure-dirs
```

## Planning docs

- `docs/ARCHITECTURE.md` outlines the intended single-package Python 3.11 architecture, end-to-end workflow, artifact layout, and core data models.
- `docs/IMPLEMENTATION_PLAN.md` describes the phased MVP delivery plan, including the requirement that the sample workflow remains runnable from checked-in `sample_data/` assets without external API keys.
- `docs/TASK_BREAKDOWN.md` defines the ordered PR-sized milestones and their done conditions.
