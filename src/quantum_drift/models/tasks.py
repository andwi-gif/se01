"""Typed data models for offline benchmark tasks and documentation excerpts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Task:
    """Represents a single Qiskit benchmark task for offline MVP pilots."""

    task_id: str
    title: str
    description: str
    prompt: str
    sdk: str
    target_versions: tuple[str, ...]
    tags: tuple[str, ...] = ()
    expected_signals: dict[str, str] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.task_id.strip():
            msg = "task_id must be non-empty"
            raise ValueError(msg)
        if self.sdk != "qiskit":
            msg = "Milestone 2 sample tasks must target the qiskit SDK"
            raise ValueError(msg)
        if not self.target_versions:
            msg = "target_versions must contain at least one SDK version"
            raise ValueError(msg)
        if any(not version.strip() for version in self.target_versions):
            msg = "target_versions cannot contain blank version strings"
            raise ValueError(msg)


@dataclass(frozen=True)
class DocumentationExcerpt:
    """Represents a local, version-specific documentation slice for retrieval."""

    excerpt_id: str
    sdk: str
    version: str
    title: str
    source_path: str
    summary: str
    content: str
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.sdk != "qiskit":
            msg = "Milestone 2 sample documentation must target the qiskit SDK"
            raise ValueError(msg)
        if not self.excerpt_id.strip() or not self.version.strip():
            msg = "excerpt_id and version must be non-empty"
            raise ValueError(msg)
        if not self.content.strip():
            msg = "content must be non-empty"
            raise ValueError(msg)


@dataclass(frozen=True)
class ModelResponseFixture:
    """Represents a deterministic offline generation fixture."""

    fixture_id: str
    task_id: str
    sdk: str
    sdk_version: str
    mode: str
    prompt_summary: str
    generated_code: str
    retrieved_context_ids: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.sdk != "qiskit":
            msg = "Milestone 2 model fixtures must target the qiskit SDK"
            raise ValueError(msg)
        if self.mode not in {"vanilla", "rag_docs", "rewrite"}:
            msg = "mode must be one of: vanilla, rag_docs, rewrite"
            raise ValueError(msg)
        if not self.generated_code.strip():
            msg = "generated_code must be non-empty"
            raise ValueError(msg)
