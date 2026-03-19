"""CLI entrypoint for the quantum_drift scaffold."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from quantum_drift.config import get_project_paths
from quantum_drift.config.loader import load_run_config
from quantum_drift.datasets import (
    load_documentation_excerpt_directory,
    load_model_response_fixtures,
    load_tasks,
)
from quantum_drift.execution import (
    load_execution_inputs,
    load_runtime_manifest,
    run_execution_pipeline,
)
from quantum_drift.generation import load_generation_inputs, run_generation_pipeline


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
    parser.add_argument(
        "--validate-config",
        type=Path,
        default=None,
        help="Load a TOML sample run config and validate the referenced offline assets.",
    )
    parser.add_argument(
        "--generate-offline",
        type=Path,
        default=None,
        help="Run the deterministic offline generation slice for a TOML config.",
    )
    parser.add_argument(
        "--execute-offline",
        type=Path,
        default=None,
        help="Execute persisted offline generation artifacts for a TOML config.",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Override the run identifier used for generation and execution artifacts.",
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

    if args.validate_config is not None:
        config = load_run_config(args.validate_config)
        tasks = load_tasks(project_paths.repo_root / config.data.task_file)
        excerpts = load_documentation_excerpt_directory(
            project_paths.repo_root / config.data.docs_path
        )
        fixtures = load_model_response_fixtures(
            project_paths.repo_root / config.data.model_response_file,
            task_ids={task.task_id for task in tasks},
            excerpt_ids={excerpt.excerpt_id for excerpt in excerpts},
        )
        print(f"Validated config: {args.validate_config}")
        print(f"Tasks loaded: {len(tasks)}")
        print(f"Documentation excerpts loaded: {len(excerpts)}")
        print(f"Model fixtures loaded: {len(fixtures)}")
        if config.execution is not None:
            runtime_manifest = load_runtime_manifest(
                project_paths.repo_root / config.execution.runtime_manifest,
                repo_root=project_paths.repo_root,
            )
            print(f"Runtime versions loaded: {len(runtime_manifest.runtimes)}")

    if args.generate_offline is not None:
        loaded = load_generation_inputs(args.generate_offline, repo_root=project_paths.repo_root)
        generation_run = run_generation_pipeline(
            loaded,
            repo_root=project_paths.repo_root,
            run_id=args.run_id,
        )
        print(f"Generated offline run: {generation_run.run_id}")
        print(f"Generation results: {len(generation_run.results)}")
        print(f"Artifacts written to: {generation_run.output_dir}")

    if args.execute_offline is not None:
        loaded_execution = load_execution_inputs(
            args.execute_offline,
            repo_root=project_paths.repo_root,
            run_id=args.run_id,
        )
        execution_run = run_execution_pipeline(loaded_execution)
        print(f"Executed offline run: {execution_run.run_id}")
        print(f"Execution results: {len(execution_run.results)}")
        print(f"Artifacts written to: {execution_run.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
