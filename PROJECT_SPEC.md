# Quantum API Drift Project Spec

## Problem
Measure how often LLM-generated quantum code that works on one SDK version breaks on later SDK versions.

## MVP objective
Deliver a demoable, reproducible end-to-end pipeline for Qiskit first.

## MVP deliverables
1. Dataset/task loader layer
2. SDK version matrix config for 2-3 Qiskit versions
3. Code generation modes:
   - vanilla
   - RAG-docs
   - rewrite baseline
4. Multi-version isolated execution harness
5. Error taxonomy classification:
   - missing or renamed symbol
   - module relocation
   - signature mismatch
   - deprecated API
   - semantic runtime error
6. Metrics:
   - exec_at_1
   - pass_at_1
   - drift_break_rate
   - rag_gain
7. Storage for runs and results
8. Streamlit dashboard for demo
9. CLI commands for pilot runs
10. Tests + GitHub Actions CI

## Required demo
The demo must show:
- one or more tasks generated and executed across multiple Qiskit versions
- at least one breakage classified into the taxonomy
- charts for exec_at_1, pass_at_1, and drift_break_rate
- comparison of vanilla vs RAG-docs vs rewrite baseline on sample data

## Constraints
- No local-machine setup required for the author
- Repo must stay runnable in CI
- If real benchmark ingestion is difficult, use clean adapters plus sample_data so the end-to-end demo still works

## Stretch goals after MVP
- Add PennyLane
- Add more benchmark tasks
- Add more model providers
- Add richer paper-ready plots
