"""Typed models for offline generation requests and persisted artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from quantum_drift.models.tasks import DocumentationExcerpt, Task

GENERATION_MODES = ("vanilla", "rag_docs", "rewrite")


@dataclass(frozen=True)
class GenerationRequest:
    """A fully resolved generation request for one task/mode/version tuple."""

    run_id: str
    task: Task
    sdk_version: str
    mode: str
    prompt: str
    retrieved_context: tuple[DocumentationExcerpt, ...] = ()
    rewrite_source: str | None = None

    def __post_init__(self) -> None:
        if not self.run_id.strip():
            msg = "run_id must be non-empty"
            raise ValueError(msg)
        if self.mode not in GENERATION_MODES:
            msg = f"unsupported generation mode: {self.mode}"
            raise ValueError(msg)
        if not self.sdk_version.strip():
            msg = "sdk_version must be non-empty"
            raise ValueError(msg)
        if not self.prompt.strip():
            msg = "prompt must be non-empty"
            raise ValueError(msg)
        if self.mode == "rewrite" and self.rewrite_source is None:
            msg = "rewrite mode requires rewrite_source"
            raise ValueError(msg)


@dataclass(frozen=True)
class GenerationResult:
    """Structured result captured for one offline generation request."""

    run_id: str
    task_id: str
    sdk: str
    sdk_version: str
    mode: str
    prompt: str
    prompt_summary: str
    generated_code: str
    backend_name: str
    fixture_id: str
    retrieved_context_ids: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.mode not in GENERATION_MODES:
            msg = f"unsupported generation mode: {self.mode}"
            raise ValueError(msg)
        if not self.generated_code.strip():
            msg = "generated_code must be non-empty"
            raise ValueError(msg)
        if not self.fixture_id.strip():
            msg = "fixture_id must be non-empty"
            raise ValueError(msg)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of the artifact."""
        return asdict(self)
