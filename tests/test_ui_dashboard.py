from __future__ import annotations

from collections.abc import Iterable
from html import escape
from pathlib import Path

from quantum_drift.cli.main import main
from quantum_drift.ui import DashboardApplication, load_dashboard_run, render_dashboard_html

REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_offline_config(tmp_path: Path) -> Path:
    task_file = (REPO_ROOT / 'sample_data/tasks/qiskit_pilot_tasks.json').as_posix()
    docs_path = (REPO_ROOT / 'sample_data/docs').as_posix()
    response_file = (
        REPO_ROOT / 'sample_data/model_responses/qiskit_saved_responses.json'
    ).as_posix()
    runtime_manifest = (REPO_ROOT / 'sample_data/configs/qiskit_runtime_manifest.toml').as_posix()
    config_path = tmp_path / 'offline_dashboard.toml'
    config_path.write_text(
        '\n'.join(
            [
                'schema_version = "1.0"',
                'output_root = "artifacts/runs"',
                '',
                '[run]',
                'name = "offline-dashboard"',
                'sdk = "qiskit"',
                'versions = ["1.0", "1.1"]',
                'modes = ["vanilla", "rag_docs"]',
                'max_tasks = 2',
                '',
                '[data]',
                f'task_file = "{task_file}"',
                f'docs_path = "{docs_path}"',
                f'model_response_file = "{response_file}"',
                '',
                '[execution]',
                f'runtime_manifest = "{runtime_manifest}"',
                'timeout_seconds = 2.0',
            ]
        )
        + '\n',
        encoding='utf-8',
    )
    return config_path


def _build_completed_run(tmp_path: Path, run_id: str = 'dashboard-test') -> Path:
    config_path = _write_offline_config(tmp_path)
    assert (
        main(
            [
                '--repo-root',
                str(tmp_path),
                '--generate-offline',
                str(config_path),
                '--run-id',
                run_id,
            ]
        )
        == 0
    )
    assert (
        main(
            [
                '--repo-root',
                str(tmp_path),
                '--execute-offline',
                str(config_path),
                '--run-id',
                run_id,
            ]
        )
        == 0
    )
    assert (
        main(
            [
                '--repo-root',
                str(tmp_path),
                '--evaluate-offline',
                str(config_path),
                '--run-id',
                run_id,
            ]
        )
        == 0
    )
    return tmp_path / f'artifacts/runs/{run_id}'


def test_load_dashboard_run_builds_joined_view_model(tmp_path: Path) -> None:
    run_dir = _build_completed_run(tmp_path)

    run_data = load_dashboard_run(run_dir)

    assert run_data.run_id == 'dashboard-test'
    assert run_data.task_count == 2
    assert run_data.attempt_count == 8
    assert tuple(group.value for group in run_data.metrics_by_sdk_version) == ('1.0', '1.1')
    assert tuple(group.value for group in run_data.metrics_by_mode) == ('rag_docs', 'vanilla')
    first_record = run_data.records[0]
    assert first_record.prompt
    assert first_record.generated_code
    assert first_record.runtime_name.startswith('qiskit-')
    assert isinstance(first_record.retrieved_context_ids, tuple)


def test_render_dashboard_html_includes_summary_and_drilldown_evidence(tmp_path: Path) -> None:
    run_dir = _build_completed_run(tmp_path)
    run_data = load_dashboard_run(run_dir)
    selected_record = run_data.records[-1]

    html = render_dashboard_html(run_data, selected_record_key=selected_record.key)

    assert 'Quantum Drift Dashboard' in html
    assert selected_record.task_id in html
    assert escape(selected_record.generated_code) in html
    assert 'SDK version metrics' in html
    assert 'Mode metrics' in html
    assert 'Execution evidence' in html


def test_dashboard_application_returns_html_for_selected_record(tmp_path: Path) -> None:
    run_dir = _build_completed_run(tmp_path)
    run_data = load_dashboard_run(run_dir)
    selected_record = run_data.records[1]
    app = DashboardApplication(run_data)
    captured: dict[str, object] = {}

    def start_response(status: str, headers: Iterable[tuple[str, str]]) -> None:
        captured['status'] = status
        captured['headers'] = tuple(headers)

    body = b''.join(
        app(
            {
                'PATH_INFO': '/',
                'QUERY_STRING': f'record={selected_record.key}',
            },
            start_response,
        )
    ).decode('utf-8')

    assert captured['status'] == '200 OK'
    assert ('Content-Type', 'text/html; charset=utf-8') in captured['headers']
    assert selected_record.task_id in body
    assert selected_record.mode in body
