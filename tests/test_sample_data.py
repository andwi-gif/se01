from __future__ import annotations

from pathlib import Path

from quantum_drift.config.loader import load_run_config
from quantum_drift.datasets import (
    load_documentation_excerpt_directory,
    load_model_response_fixtures,
    load_tasks,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_load_tasks_returns_curated_qiskit_pilot_tasks() -> None:
    tasks = load_tasks(REPO_ROOT / 'sample_data/tasks/qiskit_pilot_tasks.json')

    assert len(tasks) == 12
    assert {task.sdk for task in tasks} == {'qiskit'}
    assert {'bell_state_sampler', 'qasm_roundtrip', 'if_test_control_flow'} <= {
        task.task_id for task in tasks
    }


def test_load_run_config_and_resolve_sample_assets() -> None:
    config = load_run_config(REPO_ROOT / 'sample_data/configs/offline_pilot.toml')

    assert config.run.sdk == 'qiskit'
    assert config.run.versions == ('0.45', '1.0', '1.1')
    assert config.data.task_file == Path('sample_data/tasks/qiskit_pilot_tasks.json')


def test_load_docs_and_fixtures_validate_cross_references() -> None:
    tasks = load_tasks(REPO_ROOT / 'sample_data/tasks/qiskit_pilot_tasks.json')
    excerpts = load_documentation_excerpt_directory(REPO_ROOT / 'sample_data/docs')
    fixtures = load_model_response_fixtures(
        REPO_ROOT / 'sample_data/model_responses/qiskit_saved_responses.json',
        task_ids={task.task_id for task in tasks},
        excerpt_ids={excerpt.excerpt_id for excerpt in excerpts},
    )

    assert len(excerpts) == 12
    assert len(fixtures) == 36
    assert {fixture.mode for fixture in fixtures} == {'vanilla', 'rag_docs', 'rewrite'}
    assert all(fixture.task_id in {task.task_id for task in tasks} for fixture in fixtures)
