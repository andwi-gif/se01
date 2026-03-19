"""Project path helpers for reproducible local runs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PACKAGE_ROOT.parents[0]
REPO_ROOT = PACKAGE_ROOT.parents[1]


@dataclass(frozen=True)
class ProjectPaths:
    """Resolved repository paths used by the offline MVP scaffold."""

    repo_root: Path
    src_root: Path
    package_root: Path
    configs_dir: Path
    sample_data_dir: Path
    artifacts_dir: Path
    tests_dir: Path

    def ensure_runtime_directories(self) -> None:
        """Create directories that store reproducible local inputs and outputs."""
        runtime_directories = (
            self.configs_dir,
            self.sample_data_dir,
            self.artifacts_dir,
            self.tests_dir,
        )
        for directory in runtime_directories:
            directory.mkdir(parents=True, exist_ok=True)


def get_project_paths(repo_root: Path | None = None) -> ProjectPaths:
    """Return normalized project directories for the repository."""
    resolved_repo_root = repo_root.resolve() if repo_root is not None else REPO_ROOT
    return ProjectPaths(
        repo_root=resolved_repo_root,
        src_root=resolved_repo_root / "src",
        package_root=resolved_repo_root / "src" / "quantum_drift",
        configs_dir=resolved_repo_root / "configs",
        sample_data_dir=resolved_repo_root / "sample_data",
        artifacts_dir=resolved_repo_root / "artifacts",
        tests_dir=resolved_repo_root / "tests",
    )
