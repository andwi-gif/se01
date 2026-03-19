"""Validation helpers for sample datasets and offline fixtures."""

from __future__ import annotations

from collections.abc import Iterable

from quantum_drift.models import DocumentationExcerpt, ModelResponseFixture, Task


class ValidationError(ValueError):
    """Raised when a checked-in sample asset fails validation."""


def validate_tasks(tasks: Iterable[Task]) -> list[Task]:
    """Validate sample tasks and return them as a concrete list."""
    validated_tasks = list(tasks)
    task_ids = [task.task_id for task in validated_tasks]
    if len(task_ids) != len(set(task_ids)):
        msg = "task_ids must be unique"
        raise ValidationError(msg)
    return validated_tasks


def validate_documentation_excerpts(
    excerpts: Iterable[DocumentationExcerpt],
) -> list[DocumentationExcerpt]:
    """Validate local documentation excerpts and return them as a concrete list."""
    validated_excerpts = list(excerpts)
    excerpt_ids = [excerpt.excerpt_id for excerpt in validated_excerpts]
    if len(excerpt_ids) != len(set(excerpt_ids)):
        msg = "excerpt_ids must be unique"
        raise ValidationError(msg)
    return validated_excerpts


def validate_model_response_fixtures(
    fixtures: Iterable[ModelResponseFixture],
    *,
    task_ids: set[str],
    excerpt_ids: set[str],
) -> list[ModelResponseFixture]:
    """Validate offline generation fixtures against task and doc identifiers."""
    validated_fixtures = list(fixtures)
    fixture_ids = [fixture.fixture_id for fixture in validated_fixtures]
    if len(fixture_ids) != len(set(fixture_ids)):
        msg = "fixture_ids must be unique"
        raise ValidationError(msg)

    for fixture in validated_fixtures:
        if fixture.task_id not in task_ids:
            msg = f"Unknown task_id referenced by fixture: {fixture.task_id}"
            raise ValidationError(msg)
        missing_excerpt_ids = [
            excerpt_id
            for excerpt_id in fixture.retrieved_context_ids
            if excerpt_id not in excerpt_ids
        ]
        if missing_excerpt_ids:
            msg = (
                "Unknown documentation excerpt ids referenced by fixture: "
                + ", ".join(sorted(missing_excerpt_ids))
            )
            raise ValidationError(msg)
    return validated_fixtures
