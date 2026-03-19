"""Runtime manifest loading and deterministic runtime resolution."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quantum_drift.models.execution import RuntimeSpec


@dataclass(frozen=True)
class RuntimeManifest:
    """Runtime definitions for an SDK across supported versions."""

    sdk: str
    runtimes: dict[str, RuntimeSpec]

    def resolve(self, sdk_version: str) -> RuntimeSpec:
        """Resolve the runtime for a specific SDK version."""
        try:
            return self.runtimes[sdk_version]
        except KeyError as exc:
            msg = f"No runtime configured for sdk_version={sdk_version!r}"
            raise ValueError(msg) from exc


def load_runtime_manifest(path: Path, *, repo_root: Path) -> RuntimeManifest:
    """Load a TOML runtime manifest with deterministic local runtimes."""
    with path.open("rb") as handle:
        payload: dict[str, Any] = tomllib.load(handle)

    sdk = payload["sdk"]
    runtimes_payload = payload["runtimes"]
    runtimes: dict[str, RuntimeSpec] = {}
    for sdk_version, runtime_payload in runtimes_payload.items():
        python_entries = runtime_payload.get("python_path", [])
        python_path = tuple(_resolve_manifest_path(path, entry) for entry in python_entries)
        runtimes[sdk_version] = RuntimeSpec(
            sdk=sdk,
            sdk_version=sdk_version,
            python_executable=runtime_payload.get("python_executable", "python"),
            python_path=python_path,
            environment=dict(runtime_payload.get("environment", {})),
        )
    return RuntimeManifest(sdk=sdk, runtimes=runtimes)


def _resolve_manifest_path(manifest_path: Path, entry: str) -> Path:
    candidate = Path(entry)
    if candidate.is_absolute():
        return candidate
    return (manifest_path.parent / candidate).resolve()
