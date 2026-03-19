"""Taxonomy loading and rule models for the offline MVP."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TaxonomyLabel:
    """Metadata for one classification label."""

    name: str
    severity: str
    is_recoverable: bool
    description: str


@dataclass(frozen=True)
class TaxonomyRule:
    """Ordered matching rule for one classification label."""

    label: str
    statuses: tuple[str, ...] = ()
    timed_out: bool | None = None
    exception_types: tuple[str, ...] = ()
    exception_message_contains: tuple[str, ...] = ()
    stderr_contains: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class TaxonomyDefinition:
    """Loaded taxonomy definition from TOML."""

    labels: dict[str, TaxonomyLabel]
    rules: tuple[TaxonomyRule, ...]
    default_label: str


def load_taxonomy_definition(path: Path) -> TaxonomyDefinition:
    """Load the ordered MVP drift taxonomy from TOML."""
    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    labels = {
        name: TaxonomyLabel(
            name=name,
            severity=str(config["severity"]),
            is_recoverable=bool(config["is_recoverable"]),
            description=str(config["description"]),
        )
        for name, config in payload["labels"].items()
    }
    rules = tuple(
        TaxonomyRule(
            label=str(item["label"]),
            statuses=tuple(str(status) for status in item.get("statuses", [])),
            timed_out=item.get("timed_out"),
            exception_types=tuple(str(value) for value in item.get("exception_types", [])),
            exception_message_contains=tuple(
                str(value) for value in item.get("exception_message_contains", [])
            ),
            stderr_contains=tuple(str(value) for value in item.get("stderr_contains", [])),
            reason=str(item.get("reason", "")),
        )
        for item in payload.get("rules", [])
    )
    default_label = str(payload["default_label"])
    if default_label not in labels:
        msg = f"Unknown default taxonomy label: {default_label}"
        raise ValueError(msg)
    return TaxonomyDefinition(labels=labels, rules=rules, default_label=default_label)
