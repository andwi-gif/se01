from __future__ import annotations

from pathlib import Path

from quantum_drift.cli.main import main

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
