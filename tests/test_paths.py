from __future__ import annotations

from quantum_drift.config.paths import get_project_paths


def test_get_project_paths_matches_repo_layout(tmp_path):
    repo_root = tmp_path / "repo"
    paths = get_project_paths(repo_root)

    assert paths.repo_root == repo_root
    assert paths.package_root == repo_root / "src" / "quantum_drift"
    assert paths.configs_dir == repo_root / "configs"
    assert paths.sample_data_dir == repo_root / "sample_data"
    assert paths.artifacts_dir == repo_root / "artifacts"


def test_ensure_runtime_directories_creates_expected_folders(tmp_path):
    paths = get_project_paths(tmp_path / "repo")

    paths.ensure_runtime_directories()

    assert paths.configs_dir.is_dir()
    assert paths.sample_data_dir.is_dir()
    assert paths.artifacts_dir.is_dir()
    assert paths.tests_dir.is_dir()
