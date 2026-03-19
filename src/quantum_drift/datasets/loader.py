"""Load deterministic sample tasks, docs excerpts, and response fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from quantum_drift.datasets.validators import (
    validate_documentation_excerpts,
    validate_model_response_fixtures,
    validate_tasks,
)
from quantum_drift.models import DocumentationExcerpt, ModelResponseFixture, Task


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        msg = f"Expected JSON object at {path}"
        raise ValueError(msg)
    return payload


def load_tasks(path: Path) -> list[Task]:
    """Load task definitions from a checked-in JSON file."""
    payload = _load_json(path)
    tasks = [
        Task(
            task_id=item["task_id"],
            title=item["title"],
            description=item["description"],
            prompt=item["prompt"],
            sdk=item["sdk"],
            target_versions=tuple(item["target_versions"]),
            tags=tuple(item.get("tags", [])),
            expected_signals=item.get("expected_signals"),
            metadata=item.get("metadata", {}),
        )
        for item in payload["tasks"]
    ]
    return validate_tasks(tasks)


def load_documentation_excerpts(path: Path) -> list[DocumentationExcerpt]:
    """Load versioned documentation excerpts from a checked-in JSON file."""
    payload = _load_json(path)
    excerpts = [
        DocumentationExcerpt(
            excerpt_id=item["excerpt_id"],
            sdk=item["sdk"],
            version=item["version"],
            title=item["title"],
            source_path=item["source_path"],
            summary=item["summary"],
            content=item["content"],
            tags=tuple(item.get("tags", [])),
        )
        for item in payload["excerpts"]
    ]
    return validate_documentation_excerpts(excerpts)


def load_documentation_excerpt_directory(path: Path) -> list[DocumentationExcerpt]:
    """Load and validate all versioned documentation excerpt files in a directory."""
    excerpts: list[DocumentationExcerpt] = []
    for file_path in sorted(path.glob("*.json")):
        excerpts.extend(load_documentation_excerpts(file_path))
    return validate_documentation_excerpts(excerpts)


def load_model_response_fixtures(
    path: Path,
    *,
    task_ids: set[str],
    excerpt_ids: set[str],
) -> list[ModelResponseFixture]:
    """Load deterministic offline generation fixtures from a checked-in JSON file."""
    payload = _load_json(path)
    fixtures = [
        ModelResponseFixture(
            fixture_id=item["fixture_id"],
            task_id=item["task_id"],
            sdk=item["sdk"],
            sdk_version=item["sdk_version"],
            mode=item["mode"],
            prompt_summary=item["prompt_summary"],
            generated_code=item["generated_code"],
            retrieved_context_ids=tuple(item.get("retrieved_context_ids", [])),
            metadata=item.get("metadata", {}),
        )
        for item in payload["fixtures"]
    ]
    return validate_model_response_fixtures(fixtures, task_ids=task_ids, excerpt_ids=excerpt_ids)
