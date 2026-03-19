"""Prompt construction for deterministic offline generation modes."""

from __future__ import annotations

from dataclasses import dataclass

from quantum_drift.models import DocumentationExcerpt, Task
from quantum_drift.models.generation import GenerationRequest


@dataclass(frozen=True)
class PromptBuilder:
    """Build deterministic prompts from local tasks and documentation excerpts."""

    max_context_excerpts: int = 2

    def build_request(
        self,
        *,
        run_id: str,
        task: Task,
        sdk_version: str,
        mode: str,
        docs: tuple[DocumentationExcerpt, ...],
        rewrite_source: str | None = None,
    ) -> GenerationRequest:
        """Assemble a typed generation request for one mode."""
        retrieved_context = self._select_retrieved_context(
            task=task,
            sdk_version=sdk_version,
            docs=docs,
            mode=mode,
        )
        prompt = self._render_prompt(
            task=task,
            sdk_version=sdk_version,
            mode=mode,
            retrieved_context=retrieved_context,
            rewrite_source=rewrite_source,
        )
        return GenerationRequest(
            run_id=run_id,
            task=task,
            sdk_version=sdk_version,
            mode=mode,
            prompt=prompt,
            retrieved_context=retrieved_context,
            rewrite_source=rewrite_source,
        )

    def _select_retrieved_context(
        self,
        *,
        task: Task,
        sdk_version: str,
        docs: tuple[DocumentationExcerpt, ...],
        mode: str,
    ) -> tuple[DocumentationExcerpt, ...]:
        if mode == "vanilla" or mode == "rewrite":
            return ()
        task_terms = self._task_terms(task)
        version_docs = [excerpt for excerpt in docs if excerpt.version == sdk_version]
        scored = sorted(
            version_docs,
            key=lambda excerpt: (-self._score_excerpt(excerpt, task_terms), excerpt.excerpt_id),
        )
        selected = [excerpt for excerpt in scored if self._score_excerpt(excerpt, task_terms) > 0]
        if not selected:
            selected = scored
        return tuple(selected[: self.max_context_excerpts])

    def _task_terms(self, task: Task) -> set[str]:
        normalized = f"{task.title} {task.description} {task.prompt} {' '.join(task.tags)}".lower()
        tokens = {
            token.strip(".,:;()[]{}\n")
            for token in normalized.replace("-", " ").replace("/", " ").split()
        }
        return {token for token in tokens if token}

    def _score_excerpt(self, excerpt: DocumentationExcerpt, task_terms: set[str]) -> int:
        haystack = (
            f"{excerpt.title} {excerpt.summary} "
            f"{excerpt.content} {' '.join(excerpt.tags)}"
        ).lower()
        return sum(1 for term in task_terms if term in haystack)

    def _render_prompt(
        self,
        *,
        task: Task,
        sdk_version: str,
        mode: str,
        retrieved_context: tuple[DocumentationExcerpt, ...],
        rewrite_source: str | None,
    ) -> str:
        sections = [
            "You are generating Qiskit code for an offline API drift benchmark.",
            f"Mode: {mode}",
            f"SDK: {task.sdk}",
            f"Target SDK version: {sdk_version}",
            f"Task ID: {task.task_id}",
            f"Task Title: {task.title}",
            f"Task Description: {task.description}",
            "Instructions:",
            task.prompt,
        ]
        if mode == "rag_docs":
            context_lines = ["Retrieved local documentation context:"]
            for excerpt in retrieved_context:
                context_lines.append(
                    f"- [{excerpt.excerpt_id}] {excerpt.title} :: "
                    f"{excerpt.summary} :: {excerpt.content}"
                )
            sections.extend(context_lines)
        if mode == "rewrite" and rewrite_source is not None:
            sections.extend(
                [
                    "Rewrite baseline input code:",
                    rewrite_source,
                    (
                        "Rewrite goal: revise the baseline code to better fit "
                        "the target SDK version while staying offline-friendly."
                    ),
                ]
            )
        return "\n\n".join(sections)
