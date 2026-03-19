from __future__ import annotations

import json
from pathlib import Path

from quantum_drift.execution import (
    SubprocessExecutionRunner,
    load_execution_inputs,
    load_runtime_manifest,
    run_execution_pipeline,
)
from quantum_drift.generation import load_generation_inputs, run_generation_pipeline
from quantum_drift.models.execution import ExecutionRequest

REPO_ROOT = Path(__file__).resolve().parents[1]
TASK_FILE = (REPO_ROOT / "sample_data/tasks/qiskit_pilot_tasks.json").as_posix()
DOCS_PATH = (REPO_ROOT / "sample_data/docs").as_posix()
RESPONSE_FILE = (
    REPO_ROOT / "sample_data/model_responses/qiskit_saved_responses.json"
).as_posix()
RUNTIME_MANIFEST = (REPO_ROOT / "sample_data/configs/qiskit_runtime_manifest.toml").as_posix()


def _write_config(tmp_path: Path, *, timeout_seconds: float = 2.0) -> Path:
    config_path = tmp_path / "offline_execution.toml"
    config_path.write_text(
        "\n".join(
            [
                'schema_version = "1.0"',
                'output_root = "artifacts/runs"',
                "",
                "[run]",
                'name = "offline-exec"',
                'sdk = "qiskit"',
                'versions = ["1.0"]',
                'modes = ["vanilla", "rag_docs"]',
                "max_tasks = 3",
                "",
                "[data]",
                f'task_file = "{TASK_FILE}"',
                f'docs_path = "{DOCS_PATH}"',
                f'model_response_file = "{RESPONSE_FILE}"',
                "",
                "[execution]",
                f'runtime_manifest = "{RUNTIME_MANIFEST}"',
                f"timeout_seconds = {timeout_seconds}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return config_path


def test_runtime_manifest_resolves_versioned_stub_runtime() -> None:
    manifest = load_runtime_manifest(
        REPO_ROOT / "sample_data/configs/qiskit_runtime_manifest.toml",
        repo_root=REPO_ROOT,
    )

    runtime = manifest.resolve("1.0")

    assert runtime.sdk == "qiskit"
    assert runtime.sdk_version == "1.0"
    assert runtime.python_path
    assert runtime.python_path[0].name == "1.0"


def test_subprocess_execution_runner_captures_success_failure_and_timeout() -> None:
    manifest = load_runtime_manifest(
        REPO_ROOT / "sample_data/configs/qiskit_runtime_manifest.toml",
        repo_root=REPO_ROOT,
    )
    runtime = manifest.resolve("1.0")
    runner = SubprocessExecutionRunner()

    success = runner.run(
        ExecutionRequest(
            run_id="exec-test",
            task_id="success",
            sdk="qiskit",
            sdk_version="1.0",
            mode="vanilla",
            generated_code="from qiskit import QuantumCircuit\nprint(QuantumCircuit.__name__)\n",
        ),
        runtime=runtime,
        timeout_seconds=1.0,
    )
    failure = runner.run(
        ExecutionRequest(
            run_id="exec-test",
            task_id="failure",
            sdk="qiskit",
            sdk_version="1.0",
            mode="vanilla",
            generated_code='raise ValueError("boom")\n',
        ),
        runtime=runtime,
        timeout_seconds=1.0,
    )
    timeout = runner.run(
        ExecutionRequest(
            run_id="exec-test",
            task_id="timeout",
            sdk="qiskit",
            sdk_version="1.0",
            mode="vanilla",
            generated_code="import time\ntime.sleep(0.2)\n",
        ),
        runtime=runtime,
        timeout_seconds=0.01,
    )

    assert success.status == "success"
    assert success.exit_code == 0
    assert success.stdout.strip() == "QuantumCircuit"
    assert success.exception_type is None

    assert failure.status == "runtime_error"
    assert failure.exit_code == 1
    assert failure.exception_type == "ValueError"
    assert failure.exception_message == "boom"
    assert "Traceback" in failure.stderr

    assert timeout.status == "timeout"
    assert timeout.timed_out is True
    assert timeout.exit_code is None
    assert timeout.exception_type == "TimeoutExpired"


def test_execution_pipeline_persists_structured_artifacts(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)
    loaded_generation = load_generation_inputs(config_path, repo_root=tmp_path)
    generation_run = run_generation_pipeline(
        loaded_generation,
        repo_root=tmp_path,
        run_id="offline-exec-test",
    )

    loaded_execution = load_execution_inputs(
        config_path,
        repo_root=tmp_path,
        run_id="offline-exec-test",
    )
    execution_run = run_execution_pipeline(loaded_execution)

    assert execution_run.run_id == "offline-exec-test"
    assert len(execution_run.results) == len(generation_run.results) == 6
    assert all(result.status == "success" for result in execution_run.results)

    manifest_path = execution_run.output_dir / "execution_results.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["run_id"] == "offline-exec-test"
    assert payload["result_count"] == 6

    task_result_path = (
        execution_run.output_dir
        / "bell_state_sampler"
        / "1.0"
        / "vanilla"
        / "execution_result.json"
    )
    assert task_result_path.exists()
    task_payload = json.loads(task_result_path.read_text(encoding="utf-8"))
    assert task_payload["status"] == "success"
    assert task_payload["runtime_name"] == "qiskit-1.0"
