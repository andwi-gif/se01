"""Offline generation backends for deterministic sample runs."""

from __future__ import annotations

from dataclasses import dataclass

from quantum_drift.models import ModelResponseFixture
from quantum_drift.models.generation import GenerationRequest, GenerationResult


class BackendLookupError(LookupError):
    """Raised when no deterministic fixture matches a generation request."""


class GenerationBackend:
    """Protocol-like base class for typed generation backends."""

    name: str

    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate a result for the given request."""
        raise NotImplementedError


@dataclass(frozen=True)
class SavedResponseBackend(GenerationBackend):
    """Offline backend that serves checked-in deterministic response fixtures."""

    fixtures: tuple[ModelResponseFixture, ...]
    name: str = "saved_response"

    def select_fixture(self, request: GenerationRequest) -> ModelResponseFixture:
        """Select the best matching fixture for the request."""
        exact_match: ModelResponseFixture | None = None
        wildcard_match: ModelResponseFixture | None = None
        for fixture in self.fixtures:
            if fixture.task_id != request.task.task_id or fixture.mode != request.mode:
                continue
            if fixture.sdk_version == request.sdk_version:
                exact_match = fixture
                break
            if fixture.sdk_version == "*":
                wildcard_match = fixture
        if exact_match is not None:
            return exact_match
        if wildcard_match is not None:
            return wildcard_match
        msg = (
            "No saved-response fixture found for "
            f"task_id={request.task.task_id!r}, "
            f"sdk_version={request.sdk_version!r}, "
            f"mode={request.mode!r}"
        )
        raise BackendLookupError(msg)

    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Return a deterministic generation result from a fixture."""
        fixture = self.select_fixture(request)
        return GenerationResult(
            run_id=request.run_id,
            task_id=request.task.task_id,
            sdk=request.task.sdk,
            sdk_version=request.sdk_version,
            mode=request.mode,
            prompt=request.prompt,
            prompt_summary=fixture.prompt_summary,
            generated_code=fixture.generated_code,
            backend_name=self.name,
            fixture_id=fixture.fixture_id,
            retrieved_context_ids=tuple(
                excerpt.excerpt_id for excerpt in request.retrieved_context
            ),
            metadata={
                "fixture_metadata": fixture.metadata,
                "rewrite_source_present": request.rewrite_source is not None,
            },
        )
