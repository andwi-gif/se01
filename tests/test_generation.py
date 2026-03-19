from __future__ import annotations

import json
from pathlib import Path

from quantum_drift.generation import (
    PromptBuilder,
    load_generation_inputs,
    run_generation_pipeline,
)
from quantum_drift.generation.artifacts import write_generation_artifacts
from quantum_drift.generation.backends import SavedResponseBackend

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_prompt_builder_constructs_all_mvp_modes() -> None:
    loaded = load_generation_inputs(
        REPO_ROOT / 'sample_data/configs/offline_pilot.toml',
        repo_root=REPO_ROOT,
    )
    task = loaded.tasks[0]
    builder = PromptBuilder()

    vanilla_request = builder.build_request(
        run_id='prompt-test',
        task=task,
        sdk_version='1.0',
        mode='vanilla',
        docs=loaded.docs,
    )
    rag_request = builder.build_request(
        run_id='prompt-test',
        task=task,
        sdk_version='1.0',
        mode='rag_docs',
        docs=loaded.docs,
    )
    rewrite_request = builder.build_request(
        run_id='prompt-test',
        task=task,
        sdk_version='1.0',
        mode='rewrite',
        docs=loaded.docs,
        rewrite_source='print("baseline")\n',
    )

    assert 'Mode: vanilla' in vanilla_request.prompt
    assert vanilla_request.retrieved_context == ()
    assert 'Retrieved local documentation context:' in rag_request.prompt
    assert rag_request.retrieved_context
    assert {excerpt.version for excerpt in rag_request.retrieved_context} == {'1.0'}
    assert 'Rewrite baseline input code:' in rewrite_request.prompt
    assert rewrite_request.rewrite_source == 'print("baseline")\n'


def test_saved_response_backend_prefers_exact_fixture_selection() -> None:
    loaded = load_generation_inputs(
        REPO_ROOT / 'sample_data/configs/offline_smoke.toml',
        repo_root=REPO_ROOT,
    )
    first_fixture = loaded.fixtures[0]
    exact_fixture = first_fixture.__class__(
        fixture_id='bell_state_sampler__vanilla__1_0',
        task_id='bell_state_sampler',
        sdk='qiskit',
        sdk_version='1.0',
        mode='vanilla',
        prompt_summary='Exact fixture',
        generated_code='print("exact")\n',
        retrieved_context_ids=(),
        metadata={},
    )
    backend = SavedResponseBackend(fixtures=(exact_fixture, *loaded.fixtures))
    builder = PromptBuilder()
    request = builder.build_request(
        run_id='backend-test',
        task=loaded.tasks[0],
        sdk_version='1.0',
        mode='vanilla',
        docs=loaded.docs,
    )

    selected = backend.select_fixture(request)

    assert selected.fixture_id == 'bell_state_sampler__vanilla__1_0'


def test_offline_generation_pipeline_is_deterministic_and_persists_artifacts(
    tmp_path: Path,
) -> None:
    loaded = load_generation_inputs(
        REPO_ROOT / 'sample_data/configs/offline_smoke.toml',
        repo_root=REPO_ROOT,
    )
    run = run_generation_pipeline(loaded, repo_root=tmp_path, run_id='offline-smoke-test')

    assert run.run_id == 'offline-smoke-test'
    assert len(run.results) == 6
    first_result = run.results[0]
    assert first_result.fixture_id == 'bell_state_sampler__vanilla__any'
    assert first_result.generated_code.endswith('print("bell_state_sampler:vanilla")\n')
    rag_results = [result for result in run.results if result.mode == 'rag_docs']
    assert rag_results
    assert all(result.retrieved_context_ids for result in rag_results)

    manifest_path = run.output_dir / 'generation_results.json'
    payload = json.loads(manifest_path.read_text(encoding='utf-8'))
    assert payload['run_id'] == 'offline-smoke-test'
    assert payload['result_count'] == 6

    prompt_path = run.output_dir / 'bell_state_sampler' / '1.0' / 'rag_docs' / 'prompt.txt'
    result_path = run.output_dir / 'bell_state_sampler' / '1.0' / 'rag_docs' / 'result.json'
    assert prompt_path.exists()
    assert result_path.exists()
    assert 'Retrieved local documentation context:' in prompt_path.read_text(encoding='utf-8')


def test_write_generation_artifacts_rejects_empty_results(tmp_path: Path) -> None:
    try:
        write_generation_artifacts(output_root=tmp_path, results=())
    except ValueError as exc:
        assert 'non-empty' in str(exc)
    else:
        raise AssertionError('Expected ValueError for empty generation result set')
