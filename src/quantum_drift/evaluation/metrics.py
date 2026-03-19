"""Aggregate metric helpers for classified offline runs."""

from __future__ import annotations

from collections import Counter, defaultdict

from quantum_drift.models.evaluation import AggregateMetric, DriftClassification


def build_aggregate_metrics(
    classifications: tuple[DriftClassification, ...],
) -> tuple[AggregateMetric, ...]:
    """Compute aggregate metrics by version, mode, and label."""
    grouped: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for classification in classifications:
        grouped[("sdk_version", classification.sdk_version)][classification.label] += 1
        grouped[("mode", classification.mode)][classification.label] += 1
    metrics: list[AggregateMetric] = []
    for (dimension, value), counts in sorted(grouped.items()):
        total = sum(counts.values())
        for label, count in sorted(counts.items()):
            metrics.append(
                AggregateMetric(
                    dimension=dimension,
                    value=value,
                    label=label,
                    count=count,
                    total=total,
                    rate=count / total,
                )
            )
    return tuple(metrics)
