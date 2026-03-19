"""Classification rules that turn execution results into drift labels."""

from __future__ import annotations

from quantum_drift.evaluation.taxonomy import TaxonomyDefinition, TaxonomyRule
from quantum_drift.models.evaluation import DriftClassification
from quantum_drift.models.execution import ExecutionResult


class DriftClassifier:
    """Classify execution artifacts with an ordered taxonomy."""

    def __init__(self, taxonomy: TaxonomyDefinition) -> None:
        self._taxonomy = taxonomy

    def classify(self, result: ExecutionResult) -> DriftClassification:
        """Return the first taxonomy label matching the execution evidence."""
        matched_rule = next(
            (rule for rule in self._taxonomy.rules if _rule_matches(rule, result)),
            None,
        )
        label_name = (
            matched_rule.label
            if matched_rule is not None
            else self._taxonomy.default_label
        )
        label = self._taxonomy.labels[label_name]
        reason = matched_rule.reason if matched_rule is not None and matched_rule.reason else (
            f"Fell back to default taxonomy label: {label_name}."
        )
        return DriftClassification(
            run_id=result.run_id,
            task_id=result.task_id,
            sdk=result.sdk,
            sdk_version=result.sdk_version,
            mode=result.mode,
            label=label.name,
            severity=label.severity,
            reason=reason,
            is_recoverable=label.is_recoverable,
            execution_status=result.status,
            runtime_name=result.runtime_name,
            exit_code=result.exit_code,
            timed_out=result.timed_out,
            exception_type=result.exception_type,
            exception_message=result.exception_message,
            metadata={"taxonomy_description": label.description},
        )


def _rule_matches(rule: TaxonomyRule, result: ExecutionResult) -> bool:
    if rule.statuses and result.status not in rule.statuses:
        return False
    if rule.timed_out is not None and result.timed_out is not rule.timed_out:
        return False
    if rule.exception_types and result.exception_type not in rule.exception_types:
        return False
    if rule.exception_message_contains and not _contains_any(
        result.exception_message,
        rule.exception_message_contains,
    ):
        return False
    if rule.stderr_contains and not _contains_any(result.stderr, rule.stderr_contains):
        return False
    return True


def _contains_any(text: str | None, patterns: tuple[str, ...]) -> bool:
    if text is None:
        return False
    normalized = text.casefold()
    return any(pattern.casefold() in normalized for pattern in patterns)
