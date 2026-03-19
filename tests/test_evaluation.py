from __future__ import annotations

import json
from pathlib import Path

from quantum_drift.evaluation import (
    DriftClassifier,
    LoadedEvaluationInputs,
    load_taxonomy_definition,
    run_evaluation_pipeline,
)
from quantum_drift.models.execution import ExecutionResult

REPO_ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_PATH = REPO_ROOT / 'configs/qiskit_mvp_taxonomy.toml'


def _result(
    *,
    task_id: str,
    sdk_version: str = '1.0',
    mode: str = 'vanilla',
    status: str = 'success',
    timed_out: bool = False,
    exception_type: str | None = None,
    exception_message: str | None = None,
    stderr: str = '',
) -> ExecutionResult:
    return ExecutionResult(
        run_id='eval-test',
        task_id=task_id,
        sdk='qiskit',
        sdk_version=sdk_version,
        mode=mode,
        runtime_name=f'qiskit-{sdk_version}',
        status=status,
        exit_code=0 if status == 'success' else 1,
        stdout='',
        stderr=stderr,
        duration_seconds=0.01,
        timed_out=timed_out,
        exception_type=exception_type,
        exception_message=exception_message,
    )


def test_classifier_distinguishes_success_runtime_error_and_timeout() -> None:
    classifier = DriftClassifier(load_taxonomy_definition(TAXONOMY_PATH))

    success = classifier.classify(_result(task_id='success'))
    timeout = classifier.classify(
        _result(
            task_id='timeout',
            status='timeout',
            timed_out=True,
            exception_type='TimeoutExpired',
            exception_message='timed out',
        )
    )
    runtime_error = classifier.classify(
        _result(
            task_id='runtime-error',
            status='runtime_error',
            exception_type='ValueError',
            exception_message='unsupported observable',
            stderr='Traceback...',
        )
    )

    assert success.label == 'no_drift_success'
    assert timeout.label == 'execution_timeout'
    assert runtime_error.label == 'semantic_runtime_change'


def test_classifier_applies_ordered_rules_for_import_and_signature_cases() -> None:
    classifier = DriftClassifier(load_taxonomy_definition(TAXONOMY_PATH))

    module_path = classifier.classify(
        _result(
            task_id='module-path',
            status='runtime_error',
            exception_type='ImportError',
            exception_message="No module named 'qiskit.providers.aer'",
        )
    )
    missing_symbol = classifier.classify(
        _result(
            task_id='missing-symbol',
            status='runtime_error',
            exception_type='ImportError',
            exception_message='cannot import name Sampler from qiskit.primitives',
        )
    )
    signature_change = classifier.classify(
        _result(
            task_id='signature-change',
            status='runtime_error',
            exception_type='TypeError',
            exception_message='Sampler() got an unexpected keyword argument backend',
        )
    )

    assert module_path.label == 'module_path_change'
    assert missing_symbol.label == 'missing_symbol'
    assert signature_change.label == 'signature_change'


def test_evaluation_pipeline_aggregates_metrics_and_persists_summary(tmp_path: Path) -> None:
    output_dir = tmp_path / 'artifacts' / 'runs' / 'eval-test'
    output_dir.mkdir(parents=True)
    execution_manifest = output_dir / 'execution_results.json'
    results = [
        _result(task_id='task-a', sdk_version='1.0', mode='vanilla'),
        _result(
            task_id='task-b',
            sdk_version='1.0',
            mode='rag_docs',
            status='runtime_error',
            exception_type='AttributeError',
            exception_message='module has no attribute BackendSampler',
        ),
        _result(
            task_id='task-c',
            sdk_version='1.1',
            mode='vanilla',
            status='timeout',
            timed_out=True,
            exception_type='TimeoutExpired',
            exception_message='timed out',
        ),
        _result(
            task_id='task-d',
            sdk_version='1.1',
            mode='rag_docs',
            status='runtime_error',
            exception_type='TypeError',
            exception_message='run() got an unexpected keyword argument shots',
        ),
    ]
    execution_manifest.write_text(
        json.dumps(
            {
                'run_id': 'eval-test',
                'result_count': len(results),
                'results': [result.to_dict() for result in results],
            },
            indent=2,
        )
        + '\n',
        encoding='utf-8',
    )

    loaded = LoadedEvaluationInputs(
        output_dir=output_dir,
        execution_results=tuple(results),
        taxonomy_path=TAXONOMY_PATH,
    )

    evaluation_run = run_evaluation_pipeline(loaded)

    assert evaluation_run.run_id == 'eval-test'
    assert evaluation_run.summary.attempt_count == 4
    assert evaluation_run.summary.task_count == 4
    assert evaluation_run.summary.classification_counts == {
        'execution_timeout': 1,
        'missing_symbol': 1,
        'no_drift_success': 1,
        'signature_change': 1,
    }

    metrics = {
        (metric.dimension, metric.value, metric.label): (metric.count, metric.total, metric.rate)
        for metric in evaluation_run.summary.metrics
    }
    assert metrics[('sdk_version', '1.0', 'no_drift_success')] == (1, 2, 0.5)
    assert metrics[('sdk_version', '1.1', 'execution_timeout')] == (1, 2, 0.5)
    assert metrics[('mode', 'rag_docs', 'missing_symbol')] == (1, 2, 0.5)
    assert metrics[('mode', 'vanilla', 'no_drift_success')] == (1, 2, 0.5)

    summary_payload = json.loads((output_dir / 'run_summary.json').read_text(encoding='utf-8'))
    assert summary_payload['run_id'] == 'eval-test'
    assert summary_payload['attempt_count'] == 4

    classifications_payload = json.loads(
        (output_dir / 'drift_classifications.json').read_text(encoding='utf-8')
    )
    assert classifications_payload['classification_count'] == 4

    metric_payload = json.loads(
        (output_dir / 'metrics_by_dimension.json').read_text(encoding='utf-8')
    )
    assert metric_payload['metric_count'] == len(evaluation_run.summary.metrics)

    per_attempt_path = output_dir / 'task-d' / '1.1' / 'rag_docs' / 'drift_classification.json'
    assert per_attempt_path.exists()
    per_attempt_payload = json.loads(per_attempt_path.read_text(encoding='utf-8'))
    assert per_attempt_payload['label'] == 'signature_change'
