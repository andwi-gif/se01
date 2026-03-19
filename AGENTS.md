# AGENTS.md

## Repository goal
Build a reproducible Python research artifact and demo app for measuring quantum API drift in LLM-generated code across SDK versions.

## MVP scope
- Build the MVP first.
- MVP = Qiskit only, 2-3 SDK versions, 10-20 pilot tasks, vanilla + RAG-docs + rewrite baseline, metrics dashboard, CLI, tests, CI.
- Stretch only after MVP is green: add PennyLane, more tasks, more model backends.

## Engineering rules
- Use Python 3.11.
- Prefer a single Python codebase, not microservices.
- Use src layout.
- Public APIs must have type hints.
- Add tests for all non-trivial behavior.
- Keep configuration in YAML or TOML, not hard-coded constants.
- Do not require external API keys for tests.
- Provide a mock/saved-response model backend so the demo works without paid model access.
- Keep sample runnable data in sample_data/.
- Store run outputs in artifacts/ or outputs/.
- Update README when behavior or commands change.

## Expected modules
- datasets
- generation
- retrieval
- rewrite
- execution
- evaluation
- ui
- cli

## Validation rules
Before opening a PR:
- run lint
- run tests
- run a small pilot command end-to-end if relevant
- summarize what changed
- list remaining limitations honestly

## Done when
A task is done only if:
- code is implemented
- tests pass
- README/docs are updated
- commands to run the feature are documented
- no placeholder TODO blocks remain in the changed production path
