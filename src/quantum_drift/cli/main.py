"""CLI entrypoint for the quantum_drift scaffold."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from quantum_drift.cli.summary import (
    format_run_summary,
    load_persisted_run_summary,
    resolve_run_directory,
)
from quantum_drift.config import get_project_paths
from quantum_drift.config.loader import load_run_config
from quantum_drift.datasets import (
    load_documentation_excerpt_directory,
    load_model_response_fixtures,
    load_tasks,
)
from quantum_drift.evaluation import load_evaluation_inputs, run_evaluation_pipeline
from quantum_drift.execution import (
    load_execution_inputs,
    load_runtime_manifest,
    run_execution_pipeline,
)
from quantum_drift.generation import load_generation_inputs, run_generation_pipeline
from quantum_drift.ui import create_dashboard_server


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
        "--evaluate-offline",
        type=Path,
        default=None,
        help="Classify persisted execution artifacts and write run metrics for a TOML config.",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Override the run identifier used for generation and execution artifacts.",
    )
    parser.add_argument(
        "--dashboard-run",
        type=Path,
        default=None,
        help="Launch a local dashboard for an existing artifacts/runs/<run_id> directory.",
    )
    parser.add_argument(
        "--summary-run",
        type=str,
        default=None,
        help=(
            "Print a readable summary for an existing completed run, using either "
            "artifacts/runs/<run_id> or an explicit run directory path."
        ),
    )
    parser.add_argument(
        "--dashboard-host",
        type=str,
        default="127.0.0.1",
        help="Host interface for the local dashboard server.",
    )
    parser.add_argument(
        "--dashboard-port",
        type=int,
        default=8000,
        help="Port for the local dashboard server; use 0 to auto-select.",
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

    try:
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
            loaded = load_generation_inputs(
                args.generate_offline,
                repo_root=project_paths.repo_root,
            )
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

        if args.evaluate_offline is not None:
            loaded_evaluation = load_evaluation_inputs(
                args.evaluate_offline,
                repo_root=project_paths.repo_root,
                run_id=args.run_id,
            )
            evaluation_run = run_evaluation_pipeline(loaded_evaluation)
            print(f"Evaluated offline run: {evaluation_run.run_id}")
            print(f"Drift classifications: {len(evaluation_run.summary.classifications)}")
            print(f"Metric rows: {len(evaluation_run.summary.metrics)}")
            print(f"Artifacts written to: {evaluation_run.output_dir}")

        if args.summary_run is not None:
            summary_run_dir = resolve_run_directory(
                args.summary_run,
                repo_root=project_paths.repo_root,
            )
            persisted_summary = load_persisted_run_summary(summary_run_dir)
            print(format_run_summary(persisted_summary))

        if args.dashboard_run is not None:
            server, url = create_dashboard_server(
                args.dashboard_run,
                host=args.dashboard_host,
                port=args.dashboard_port,
            )
            print(f"Dashboard run: {args.dashboard_run}")
            print(f"Dashboard URL: {url}")
            print("Press Ctrl+C to stop the dashboard server.")
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                print("Dashboard server stopped.")
            finally:
                server.server_close()
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(_format_cli_error(exc, project_paths.repo_root), file=sys.stderr)
        return 2
    return 0


def _format_cli_error(exc: Exception, repo_root: Path) -> str:
    """Convert common offline workflow failures into concise CLI guidance."""
    if isinstance(exc, FileNotFoundError):
        missing_path = Path(exc.filename) if exc.filename is not None else None
        if missing_path is not None:
            if missing_path.name == "generation_results.json":
                return (
                    "Error: offline execution could not find generation artifacts at "
                    f"{missing_path}. Run --generate-offline first for the same --run-id."
                )
            if missing_path.name == "execution_results.json":
                return (
                    "Error: offline evaluation could not find execution artifacts at "
                    f"{missing_path}. Run --execute-offline first for the same --run-id."
                )
            if missing_path.name in {"run_summary.json", "metrics_by_dimension.json"}:
                return (
                    "Error: summary data is incomplete for "
                    f"{missing_path.parent}. Run --evaluate-offline first for that run."
                )
            if not missing_path.is_absolute():
                missing_path = (repo_root / missing_path).resolve()
            return f"Error: required file or directory was not found: {missing_path}"
        return f"Error: required file or directory was not found: {exc}"
    if isinstance(exc, KeyError):
        return f"Error: persisted artifact is missing expected field {exc!s}."
    return f"Error: {exc}"


if __name__ == "__main__":
    raise SystemExit(main())
