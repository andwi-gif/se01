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
