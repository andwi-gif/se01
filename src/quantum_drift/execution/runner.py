"""Subprocess-based execution harness for offline generated code."""

from __future__ import annotations

import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Literal, Protocol

from quantum_drift.models.execution import ExecutionRequest, ExecutionResult, RuntimeSpec


class ExecutionRunner(Protocol):
    """Protocol for executing generated candidates in a selected runtime."""

    def run(
        self,
        request: ExecutionRequest,
        *,
        runtime: RuntimeSpec,
        timeout_seconds: float,
    ) -> ExecutionResult:
        """Execute one generated candidate and capture the outcome."""


class SubprocessExecutionRunner:
    """Execute generated code in a subprocess with deterministic runtime wiring."""

    def run(
        self,
        request: ExecutionRequest,
        *,
        runtime: RuntimeSpec,
        timeout_seconds: float,
    ) -> ExecutionResult:
        start = time.perf_counter()
        with tempfile.TemporaryDirectory(prefix="quantum-drift-exec-") as temp_dir:
            script_path = Path(temp_dir) / "candidate.py"
            script_path.write_text(request.generated_code, encoding="utf-8")
            env = self._build_env(runtime)
            try:
                completed = subprocess.run(
                    [runtime.python_executable, str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                    check=False,
                    env=env,
                )
            except subprocess.TimeoutExpired as exc:
                duration = time.perf_counter() - start
                return ExecutionResult(
                    run_id=request.run_id,
                    task_id=request.task_id,
                    sdk=request.sdk,
                    sdk_version=request.sdk_version,
                    mode=request.mode,
                    runtime_name=f"{runtime.sdk}-{runtime.sdk_version}",
                    status="timeout",
                    exit_code=None,
                    stdout=_coerce_subprocess_output(exc.stdout),
                    stderr=_coerce_subprocess_output(exc.stderr),
                    duration_seconds=duration,
                    timed_out=True,
                    exception_type=exc.__class__.__name__,
                    exception_message=str(exc),
                )
            except OSError as exc:
                duration = time.perf_counter() - start
                return ExecutionResult(
                    run_id=request.run_id,
                    task_id=request.task_id,
                    sdk=request.sdk,
                    sdk_version=request.sdk_version,
                    mode=request.mode,
                    runtime_name=f"{runtime.sdk}-{runtime.sdk_version}",
                    status="runner_error",
                    exit_code=None,
                    stdout="",
                    stderr="",
                    duration_seconds=duration,
                    timed_out=False,
                    exception_type=exc.__class__.__name__,
                    exception_message=str(exc),
                )

        duration = time.perf_counter() - start
        status: Literal["success", "runtime_error"] = (
            "success" if completed.returncode == 0 else "runtime_error"
        )
        exception_type, exception_message = _parse_python_exception(completed.stderr)
        return ExecutionResult(
            run_id=request.run_id,
            task_id=request.task_id,
            sdk=request.sdk,
            sdk_version=request.sdk_version,
            mode=request.mode,
            runtime_name=f"{runtime.sdk}-{runtime.sdk_version}",
            status=status,
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            duration_seconds=duration,
            timed_out=False,
            exception_type=exception_type,
            exception_message=exception_message,
        )

    def _build_env(self, runtime: RuntimeSpec) -> dict[str, str]:
        env = os.environ.copy()
        python_path_entries = [str(path) for path in runtime.python_path]
        existing_pythonpath = env.get("PYTHONPATH")
        if existing_pythonpath:
            python_path_entries.append(existing_pythonpath)
        if python_path_entries:
            env["PYTHONPATH"] = os.pathsep.join(python_path_entries)
        env.update(runtime.environment)
        return env


def _parse_python_exception(stderr: str) -> tuple[str | None, str | None]:
    if not stderr.strip():
        return (None, None)
    final_line = stderr.strip().splitlines()[-1]
    if ":" not in final_line:
        return (None, final_line)
    exception_type, exception_message = final_line.split(":", 1)
    return (exception_type.strip() or None, exception_message.strip() or None)


def _coerce_subprocess_output(output: bytes | str | None) -> str:
    if output is None:
        return ""
    if isinstance(output, bytes):
        return output.decode("utf-8", errors="replace")
    return output
