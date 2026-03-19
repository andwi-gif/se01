from __future__ import annotations

from pathlib import Path

from quantum_drift.cli.main import main
from quantum_drift.cli.summary import format_run_summary, load_persisted_run_summary

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_cli_main_prints_workspace_paths(capsys):
    exit_code = main(['--ensure-dirs'])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert 'Repository root:' in captured.out
    assert 'Sample data:' in captured.out


def test_cli_can_validate_offline_sample_config(capsys) -> None:
    exit_code = main(
        [
            '--validate-config',
            str(REPO_ROOT / 'sample_data/configs/offline_smoke.toml'),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert 'Validated config:' in captured.out
    assert 'Tasks loaded: 12' in captured.out
    assert 'Documentation excerpts loaded: 12' in captured.out
    assert 'Model fixtures loaded: 36' in captured.out


def test_cli_can_run_offline_generation(tmp_path: Path, capsys) -> None:
    task_file = (REPO_ROOT / 'sample_data/tasks/qiskit_pilot_tasks.json').as_posix()
    docs_path = (REPO_ROOT / 'sample_data/docs').as_posix()
    response_file = (
        REPO_ROOT / 'sample_data/model_responses/qiskit_saved_responses.json'
    ).as_posix()
    config_path = tmp_path / 'offline_cli.toml'
    config_path.write_text(
        '\n'.join(
            [
                'schema_version = "1.0"',
                'output_root = "artifacts/runs"',
                '',
                '[run]',
                'name = "offline-cli"',
                'sdk = "qiskit"',
                'versions = ["1.0"]',
                'modes = ["vanilla", "rag_docs"]',
                'max_tasks = 3',
                '',
                '[data]',
                f'task_file = "{task_file}"',
                f'docs_path = "{docs_path}"',
                f'model_response_file = "{response_file}"',
            ]
        )
        + '\n',
        encoding='utf-8',
    )

    exit_code = main(
        [
            '--repo-root',
            str(tmp_path),
            '--generate-offline',
            str(config_path),
            '--run-id',
            'cli-offline-test',
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert 'Generated offline run: cli-offline-test' in captured.out
    assert 'Generation results: 6' in captured.out
    assert (tmp_path / 'artifacts/runs/cli-offline-test/generation_results.json').exists()


def test_cli_can_execute_offline_generation(tmp_path: Path, capsys) -> None:
    task_file = (REPO_ROOT / 'sample_data/tasks/qiskit_pilot_tasks.json').as_posix()
    docs_path = (REPO_ROOT / 'sample_data/docs').as_posix()
    response_file = (
        REPO_ROOT / 'sample_data/model_responses/qiskit_saved_responses.json'
    ).as_posix()
    runtime_manifest = (REPO_ROOT / 'sample_data/configs/qiskit_runtime_manifest.toml').as_posix()
    config_path = tmp_path / 'offline_cli_execution.toml'
    config_path.write_text(
        '\n'.join(
            [
                'schema_version = "1.0"',
                'output_root = "artifacts/runs"',
                '',
                '[run]',
                'name = "offline-cli-exec"',
                'sdk = "qiskit"',
                'versions = ["1.0"]',
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

    generation_exit_code = main(
        [
            '--repo-root',
            str(tmp_path),
            '--generate-offline',
            str(config_path),
            '--run-id',
            'cli-execution-test',
        ]
    )
    execution_exit_code = main(
        [
            '--repo-root',
            str(tmp_path),
            '--execute-offline',
            str(config_path),
            '--run-id',
            'cli-execution-test',
        ]
    )

    captured = capsys.readouterr()

    assert generation_exit_code == 0
    assert execution_exit_code == 0
    assert 'Executed offline run: cli-execution-test' in captured.out
    assert 'Execution results: 4' in captured.out
    assert (tmp_path / 'artifacts/runs/cli-execution-test/execution_results.json').exists()




def test_cli_can_evaluate_offline_run(tmp_path: Path, capsys) -> None:
    task_file = (REPO_ROOT / 'sample_data/tasks/qiskit_pilot_tasks.json').as_posix()
    docs_path = (REPO_ROOT / 'sample_data/docs').as_posix()
    response_file = (
        REPO_ROOT / 'sample_data/model_responses/qiskit_saved_responses.json'
    ).as_posix()
    runtime_manifest = (REPO_ROOT / 'sample_data/configs/qiskit_runtime_manifest.toml').as_posix()
    config_path = tmp_path / 'offline_cli_evaluation.toml'
    config_path.write_text(
        '\n'.join(
            [
                'schema_version = "1.0"',
                'output_root = "artifacts/runs"',
                '',
                '[run]',
                'name = "offline-cli-eval"',
                'sdk = "qiskit"',
                'versions = ["1.0"]',
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

    assert (
        main(
            [
                '--repo-root',
                str(tmp_path),
                '--generate-offline',
                str(config_path),
                '--run-id',
                'cli-eval-test',
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
                'cli-eval-test',
            ]
        )
        == 0
    )
    evaluation_exit_code = main(
        [
            '--repo-root',
            str(tmp_path),
            '--evaluate-offline',
            str(config_path),
            '--run-id',
            'cli-eval-test',
        ]
    )

    captured = capsys.readouterr()

    assert evaluation_exit_code == 0
    assert 'Evaluated offline run: cli-eval-test' in captured.out
    assert 'Drift classifications: 4' in captured.out
    assert (tmp_path / 'artifacts/runs/cli-eval-test/run_summary.json').exists()


def test_cli_can_print_saved_summary_from_run_directory(tmp_path: Path, capsys) -> None:
    task_file = (REPO_ROOT / 'sample_data/tasks/qiskit_pilot_tasks.json').as_posix()
    docs_path = (REPO_ROOT / 'sample_data/docs').as_posix()
    response_file = (
        REPO_ROOT / 'sample_data/model_responses/qiskit_saved_responses.json'
    ).as_posix()
    runtime_manifest = (REPO_ROOT / 'sample_data/configs/qiskit_runtime_manifest.toml').as_posix()
    config_path = tmp_path / 'offline_cli_summary.toml'
    config_path.write_text(
        '\n'.join(
            [
                'schema_version = "1.0"',
                'output_root = "artifacts/runs"',
                '',
                '[run]',
                'name = "offline-cli-summary"',
                'sdk = "qiskit"',
                'versions = ["1.0"]',
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

    for command in ('--generate-offline', '--execute-offline', '--evaluate-offline'):
        assert (
            main(
                [
                    '--repo-root',
                    str(tmp_path),
                    command,
                    str(config_path),
                    '--run-id',
                    'cli-summary-test',
                ]
            )
            == 0
        )

    summary_exit_code = main(
        [
            '--repo-root',
            str(tmp_path),
            '--summary-run',
            str(tmp_path / 'artifacts/runs/cli-summary-test'),
        ]
    )

    captured = capsys.readouterr()

    assert summary_exit_code == 0
    assert 'Run ID: cli-summary-test' in captured.out
    assert 'Task count: 2' in captured.out
    assert 'Attempt count: 4' in captured.out
    assert 'SDK versions: 1.0' in captured.out
    assert 'Generation modes: rag_docs, vanilla' in captured.out
    assert 'Drift label counts:' in captured.out
    assert 'Aggregate metrics by dimension:' in captured.out


def test_cli_can_print_saved_summary_from_run_id(tmp_path: Path, capsys) -> None:
    run_dir = tmp_path / 'artifacts/runs/existing-run'
    run_dir.mkdir(parents=True)
    (run_dir / 'run_summary.json').write_text(
        '\n'.join(
            [
                '{',
                '  "run_id": "existing-run",',
                '  "task_count": 2,',
                '  "attempt_count": 4,',
                '  "sdk_versions": ["0.45", "1.0"],',
                '  "modes": ["vanilla", "rewrite"],',
                '  "labels": ["missing_symbol", "no_drift_success"],',
                '  "classifications": [],',
                '  "metrics": [],',
                '  "classification_counts": {"missing_symbol": 1, "no_drift_success": 3},',
                f'  "artifact_root": "{run_dir.as_posix()}"',
                '}',
            ]
        )
        + '\n',
        encoding='utf-8',
    )
    (run_dir / 'metrics_by_dimension.json').write_text(
        '\n'.join(
            [
                '{',
                '  "run_id": "existing-run",',
                '  "metric_count": 2,',
                '  "metrics": [',
                '    {"dimension": "mode", "value": "vanilla",',
                '     "label": "no_drift_success", "count": 2, "total": 2, "rate": 1.0},',
                '    {"dimension": "sdk_version", "value": "1.0",',
                '     "label": "missing_symbol", "count": 1, "total": 2, "rate": 0.5}',
                '  ]',
                '}',
            ]
        )
        + '\n',
        encoding='utf-8',
    )

    summary_exit_code = main(
        [
            '--repo-root',
            str(tmp_path),
            '--summary-run',
            'existing-run',
        ]
    )

    captured = capsys.readouterr()

    assert summary_exit_code == 0
    assert 'Run ID: existing-run' in captured.out
    assert 'SDK versions: 0.45, 1.0' in captured.out
    assert 'Generation modes: vanilla, rewrite' in captured.out
    assert 'vanilla | no_drift_success | count=2/2 (100.0%)' in captured.out
    assert '1.0 | missing_symbol | count=1/2 (50.0%)' in captured.out


def test_format_run_summary_renders_grouped_metric_sections(tmp_path: Path) -> None:
    run_dir = tmp_path / 'artifacts/runs/unit-summary'
    run_dir.mkdir(parents=True)
    (run_dir / 'run_summary.json').write_text(
        '\n'.join(
            [
                '{',
                '  "run_id": "unit-summary",',
                '  "task_count": 1,',
                '  "attempt_count": 2,',
                '  "sdk_versions": ["1.1"],',
                '  "modes": ["rag_docs", "vanilla"],',
                '  "labels": ["no_drift_success"],',
                '  "classifications": [],',
                '  "metrics": [],',
                '  "classification_counts": {"no_drift_success": 2},',
                f'  "artifact_root": "{run_dir.as_posix()}"',
                '}',
            ]
        )
        + '\n',
        encoding='utf-8',
    )
    (run_dir / 'metrics_by_dimension.json').write_text(
        '\n'.join(
            [
                '{',
                '  "run_id": "unit-summary",',
                '  "metric_count": 2,',
                '  "metrics": [',
                '    {"dimension": "mode", "value": "rag_docs",',
                '     "label": "no_drift_success", "count": 1, "total": 1, "rate": 1.0},',
                '    {"dimension": "sdk_version", "value": "1.1",',
                '     "label": "no_drift_success", "count": 2, "total": 2, "rate": 1.0}',
                '  ]',
                '}',
            ]
        )
        + '\n',
        encoding='utf-8',
    )

    rendered = format_run_summary(load_persisted_run_summary(run_dir))

    assert 'Summary run directory:' in rendered
    assert 'Drift label counts:' in rendered
    assert '  mode:' in rendered
    assert '  sdk_version:' in rendered
