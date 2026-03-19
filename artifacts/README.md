# Artifacts

Runtime outputs, reports, and pilot run directories should be written under this folder.

For the offline Qiskit MVP, each run under `artifacts/runs/<run_id>/` may now contain:

- `generation_results.json`
- `execution_results.json`
- `drift_classifications.json`
- `metrics_by_dimension.json`
- `run_summary.json`
- per-attempt task/version/mode subdirectories containing generation, execution, and classification artifacts
