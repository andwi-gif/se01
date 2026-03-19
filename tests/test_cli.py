from __future__ import annotations

from quantum_drift.cli.main import main


def test_cli_main_prints_workspace_paths(capsys):
    exit_code = main(["--ensure-dirs"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Repository root:" in captured.out
    assert "Sample data:" in captured.out
