"""Minimal local dashboard for inspecting persisted offline run artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from html import escape
from http import HTTPStatus
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs
from wsgiref.simple_server import WSGIServer, make_server


@dataclass(frozen=True)
class DashboardMetricGroup:
    """Metrics grouped for one dimension value."""

    value: str
    total: int
    label_counts: dict[str, int]
    label_rates: dict[str, float]


@dataclass(frozen=True)
class DashboardRecord:
    """Joined per-attempt record used by the dashboard drill-down."""

    task_id: str
    sdk_version: str
    mode: str
    label: str
    severity: str
    execution_status: str
    prompt: str
    generated_code: str
    stdout: str
    stderr: str
    metadata: dict[str, Any]
    retrieved_context_ids: tuple[str, ...]
    exception_type: str | None
    exception_message: str | None
    exit_code: int | None
    timed_out: bool
    runtime_name: str

    @property
    def key(self) -> str:
        """Return a stable identifier for query-string selection."""
        return f"{self.task_id}|{self.sdk_version}|{self.mode}"


@dataclass(frozen=True)
class DashboardRunData:
    """View model for the local run dashboard."""

    run_dir: Path
    run_id: str
    task_count: int
    attempt_count: int
    classification_counts: dict[str, int]
    sdk_versions: tuple[str, ...]
    modes: tuple[str, ...]
    metrics_by_sdk_version: tuple[DashboardMetricGroup, ...]
    metrics_by_mode: tuple[DashboardMetricGroup, ...]
    records: tuple[DashboardRecord, ...]


def load_dashboard_run(run_dir: Path) -> DashboardRunData:
    """Load a completed run directory into a dashboard-friendly view model."""
    resolved_run_dir = run_dir.resolve()
    summary = _read_json(resolved_run_dir / "run_summary.json")
    metrics_payload = _read_json(resolved_run_dir / "metrics_by_dimension.json")
    classifications_payload = _read_json(resolved_run_dir / "drift_classifications.json")
    generation_payload = _read_json(resolved_run_dir / "generation_results.json")
    execution_payload = _read_json(resolved_run_dir / "execution_results.json")

    metrics = metrics_payload["metrics"]
    classifications = classifications_payload["classifications"]
    generation_results = _index_records(generation_payload["results"])
    execution_results = _index_records(execution_payload["results"])

    records: list[DashboardRecord] = []
    for classification in sorted(
        classifications,
        key=lambda item: (item["task_id"], item["sdk_version"], item["mode"]),
    ):
        record_key = _record_key(classification)
        generation = generation_results[record_key]
        execution = execution_results[record_key]
        records.append(
            DashboardRecord(
                task_id=classification["task_id"],
                sdk_version=classification["sdk_version"],
                mode=classification["mode"],
                label=classification["label"],
                severity=classification["severity"],
                execution_status=classification["execution_status"],
                prompt=generation["prompt"],
                generated_code=generation["generated_code"],
                stdout=execution["stdout"],
                stderr=execution["stderr"],
                metadata=classification["metadata"],
                retrieved_context_ids=tuple(generation.get("retrieved_context_ids", [])),
                exception_type=execution.get("exception_type"),
                exception_message=execution.get("exception_message"),
                exit_code=execution.get("exit_code"),
                timed_out=bool(execution["timed_out"]),
                runtime_name=execution["runtime_name"],
            )
        )

    return DashboardRunData(
        run_dir=resolved_run_dir,
        run_id=summary["run_id"],
        task_count=summary["task_count"],
        attempt_count=summary["attempt_count"],
        classification_counts=dict(summary["classification_counts"]),
        sdk_versions=tuple(summary["sdk_versions"]),
        modes=tuple(summary["modes"]),
        metrics_by_sdk_version=_group_metrics(metrics, dimension="sdk_version"),
        metrics_by_mode=_group_metrics(metrics, dimension="mode"),
        records=tuple(records),
    )


class DashboardApplication:
    """WSGI application that renders a single-run local dashboard."""

    def __init__(self, run_data: DashboardRunData):
        self._run_data = run_data

    def __call__(self, environ: dict[str, Any], start_response: Any) -> list[bytes]:
        path = environ.get("PATH_INFO", "/")
        if path != "/":
            start_response(
                f"{HTTPStatus.NOT_FOUND.value} {HTTPStatus.NOT_FOUND.phrase}",
                [("Content-Type", "text/plain; charset=utf-8")],
            )
            return [b"Not found"]

        query = parse_qs(environ.get("QUERY_STRING", ""), keep_blank_values=False)
        selected = query.get("record", [None])[0]
        html = render_dashboard_html(self._run_data, selected_record_key=selected)
        start_response(
            f"{HTTPStatus.OK.value} {HTTPStatus.OK.phrase}",
            [("Content-Type", "text/html; charset=utf-8")],
        )
        return [html.encode("utf-8")]


def create_dashboard_server(
    run_dir: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
) -> tuple[WSGIServer, str]:
    """Create a local HTTP server for one persisted run directory."""
    run_data = load_dashboard_run(run_dir)
    httpd = make_server(host, port, DashboardApplication(run_data))
    server_host, server_port = httpd.server_address[:2]
    if isinstance(server_host, bytes):
        resolved_host = server_host.decode("utf-8")
    else:
        resolved_host = str(server_host)
    url = f"http://{resolved_host}:{server_port}/"
    return httpd, url


def render_dashboard_html(
    run_data: DashboardRunData,
    selected_record_key: str | None = None,
) -> str:
    """Render the single-run dashboard as a standalone HTML page."""
    selected_record = _select_record(run_data.records, selected_record_key)
    sidebar_rows = "\n".join(
        _render_record_link(record, selected_record) for record in run_data.records
    )
    summary_cards = "\n".join(
        [
            _render_summary_card("Run ID", run_data.run_id),
            _render_summary_card("Tasks", str(run_data.task_count)),
            _render_summary_card("Attempts", str(run_data.attempt_count)),
            _render_summary_card(
                "Labels",
                ", ".join(
                    f"{label}: {count}"
                    for label, count in sorted(run_data.classification_counts.items())
                ),
            ),
        ]
    )
    sdk_table = _render_metric_table("SDK version metrics", run_data.metrics_by_sdk_version)
    mode_table = _render_metric_table("Mode metrics", run_data.metrics_by_mode)
    drilldown = _render_drilldown(selected_record)
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <title>Quantum Drift Dashboard - {escape(run_data.run_id)}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; background: #f6f7fb; color: #1f2937; }}
    header {{ padding: 1.5rem 2rem; background: #111827; color: white; }}
    main {{ display: grid; grid-template-columns: 22rem 1fr; min-height: calc(100vh - 88px); }}
    aside {{ border-right: 1px solid #d1d5db; background: white; padding: 1rem; overflow-y: auto; }}
    section {{ padding: 1.5rem 2rem; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr));
             gap: 1rem; margin-bottom: 1.5rem; }}
    .card, .panel {{ background: white; border: 1px solid #d1d5db; border-radius: 8px;
                    padding: 1rem; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }}
    .record-link {{ display: block; padding: 0.75rem; border: 1px solid #d1d5db;
                   border-radius: 8px; text-decoration: none; color: inherit;
                   margin-bottom: 0.75rem; }}
    .record-link.active {{ border-color: #2563eb; background: #eff6ff; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ text-align: left; padding: 0.5rem; border-bottom: 1px solid #e5e7eb;
             vertical-align: top; }}
    pre {{ background: #111827; color: #f9fafb; padding: 1rem; border-radius: 8px;
            overflow-x: auto; white-space: pre-wrap; }}
    .grid-two {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(18rem, 1fr));
                gap: 1rem; margin-bottom: 1.5rem; }}
    code {{ font-family: Consolas, monospace; }}
  </style>
</head>
<body>
<header>
  <h1>Quantum Drift Dashboard</h1>
  <p>Run directory: <code>{escape(str(run_data.run_dir))}</code></p>
</header>
<main>
  <aside>
    <h2>Task drill-down</h2>
    {sidebar_rows}
  </aside>
  <section>
    <div class=\"cards\">{summary_cards}</div>
    <div class=\"grid-two\">
      <div class=\"panel\">{sdk_table}</div>
      <div class=\"panel\">{mode_table}</div>
    </div>
    <div class=\"panel\">{drilldown}</div>
  </section>
</main>
</body>
</html>
"""


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        msg = f"expected JSON object at {path}"
        raise ValueError(msg)
    return payload


def _record_key(payload: dict[str, Any]) -> tuple[str, str, str]:
    return payload["task_id"], payload["sdk_version"], payload["mode"]


def _index_records(payloads: list[dict[str, Any]]) -> dict[tuple[str, str, str], dict[str, Any]]:
    return {_record_key(payload): payload for payload in payloads}


def _group_metrics(
    metrics: list[dict[str, Any]],
    *,
    dimension: str,
) -> tuple[DashboardMetricGroup, ...]:
    grouped: dict[str, dict[str, Any]] = {}
    for metric in metrics:
        if metric["dimension"] != dimension:
            continue
        group = grouped.setdefault(
            metric["value"],
            {"total": metric["total"], "counts": {}, "rates": {}},
        )
        group["counts"][metric["label"]] = metric["count"]
        group["rates"][metric["label"]] = metric["rate"]
    return tuple(
        DashboardMetricGroup(
            value=value,
            total=grouped[value]["total"],
            label_counts=dict(sorted(grouped[value]["counts"].items())),
            label_rates=dict(sorted(grouped[value]["rates"].items())),
        )
        for value in sorted(grouped)
    )


def _select_record(
    records: tuple[DashboardRecord, ...],
    selected_record_key: str | None,
) -> DashboardRecord:
    if selected_record_key is not None:
        for record in records:
            if record.key == selected_record_key:
                return record
    return records[0]


def _render_summary_card(title: str, value: str) -> str:
    return f"<div class=\"card\"><strong>{escape(title)}</strong><div>{escape(value)}</div></div>"


def _render_metric_table(title: str, groups: tuple[DashboardMetricGroup, ...]) -> str:
    rows: list[str] = []
    for group in groups:
        label_summary = "<br>".join(
            f"{escape(label)}: {count} ({rate:.0%})"
            for label, count in group.label_counts.items()
            for rate in [group.label_rates[label]]
        )
        rows.append(
            "<tr>"
            f"<td>{escape(group.value)}</td>"
            f"<td>{group.total}</td>"
            f"<td>{label_summary}</td>"
            "</tr>"
        )
    table_body = "\n".join(rows)
    return (
        f"<h2>{escape(title)}</h2>"
        "<table><thead><tr><th>Value</th><th>Total</th><th>Label breakdown</th></tr></thead>"
        f"<tbody>{table_body}</tbody></table>"
    )


def _render_record_link(record: DashboardRecord, selected_record: DashboardRecord) -> str:
    classes = "record-link active" if record.key == selected_record.key else "record-link"
    return (
        f"<a class=\"{classes}\" href=\"/?record={escape(record.key)}\">"
        f"<strong>{escape(record.task_id)}</strong><br>"
        f"SDK {escape(record.sdk_version)} · {escape(record.mode)}<br>"
        f"Label: {escape(record.label)}"
        "</a>"
    )


def _render_drilldown(record: DashboardRecord) -> str:
    metadata_items = "".join(
        f"<li><strong>{escape(str(key))}</strong>: {escape(str(value))}</li>"
        for key, value in sorted(record.metadata.items())
    )
    retrieved_context = (
        ", ".join(record.retrieved_context_ids)
        if record.retrieved_context_ids
        else "(none)"
    )
    exception_bits = []
    if record.exception_type is not None:
        exception_bits.append(f"Type: {escape(record.exception_type)}")
    if record.exception_message is not None:
        exception_bits.append(f"Message: {escape(record.exception_message)}")
    exception_summary = "<br>".join(exception_bits) if exception_bits else "No parsed exception"
    metadata_block = f"<ul>{metadata_items}</ul>" if metadata_items else "<p>No extra metadata</p>"
    return f"""
<h2>Selected record</h2>
<p><strong>Task:</strong> {escape(record.task_id)}<br>
<strong>SDK version:</strong> {escape(record.sdk_version)}<br>
<strong>Mode:</strong> {escape(record.mode)}<br>
<strong>Label:</strong> {escape(record.label)} ({escape(record.severity)})<br>
<strong>Execution status:</strong> {escape(record.execution_status)}<br>
<strong>Runtime:</strong> {escape(record.runtime_name)}<br>
<strong>Exit code:</strong> {escape(str(record.exit_code))}<br>
<strong>Timed out:</strong> {escape(str(record.timed_out))}<br>
<strong>Retrieved context ids:</strong> {escape(retrieved_context)}</p>
<h3>Prompt</h3>
<pre>{escape(record.prompt)}</pre>
<h3>Generated code</h3>
<pre>{escape(record.generated_code)}</pre>
<div class=\"grid-two\">
  <div>
    <h3>Stdout</h3>
    <pre>{escape(record.stdout or '(empty)')}</pre>
  </div>
  <div>
    <h3>Stderr</h3>
    <pre>{escape(record.stderr or '(empty)')}</pre>
  </div>
</div>
<h3>Execution evidence</h3>
<p>{exception_summary}</p>
<h3>Classification metadata</h3>
{metadata_block}
"""
