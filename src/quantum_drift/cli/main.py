"""CLI entrypoint for the quantum_drift scaffold."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from quantum_drift.config.paths import get_project_paths


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level CLI parser."""
    parser = argparse.ArgumentParser(
        prog="quantum-drift",
        description="Bootstrap and inspect the local quantum drift research workspace.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Override the repository root used to resolve project directories.",
    )
    parser.add_argument(
        "--ensure-dirs",
        action="store_true",
        help="Create the expected local directories if they do not already exist.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the scaffold CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    project_paths = get_project_paths(args.repo_root)

    if args.ensure_dirs:
        project_paths.ensure_runtime_directories()

    print(f"Repository root: {project_paths.repo_root}")
    print(f"Package root: {project_paths.package_root}")
    print(f"Configs: {project_paths.configs_dir}")
    print(f"Sample data: {project_paths.sample_data_dir}")
    print(f"Artifacts: {project_paths.artifacts_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
