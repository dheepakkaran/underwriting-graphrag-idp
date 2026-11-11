# BUILD-LOG (2026-11-11)

Built in one Claude Code session (Claude Code = the coding agent that wrote the code from a written, time-boxed build
plan). Dheepak supplied the API key and the go-ahead for a capped Claude Haiku run.

## Done
- Discovery docs, generator, internal records, frozen rules baseline (commit 1)
- Schema, validators with quote grounding, graph, vector RAG, LangGraph agent with interrupt, FastAPI + UI, Dockerfile, 14 tests (commit 2)
- Prompt v2 frozen on dev; agent iterations 1–3 on dev; agent frozen (commits 3–4)
- Test runs once; RESULTS.md generated from results/; FAILURES, HANDOVER, demo script, sprint log

## Corrected during the build (by review of outputs, not by changing test data)
- Regex baseline completed for the one-row form before freezing (FAILURES #1)
- Prompt v2 for verbatim quotes (#2); agent guardrail then narrowed scope (#3, #4)
- `sentence-transformers` in the plan swapped for `fastembed` (same bge-small-en-v1.5 model, ONNX, much lighter install)

## Docker (2026-11-11)
- Fixed before the first build: `uv export --no-emit-project`, `.dockerignore` (keeps `.venv`, `.env`, PDFs out of the image)
- `docker_smoke.sh` run by Dheepak (sudo; group not active in the coding session): /health 60/60, /queue 29, UI 200

## Remaining
- Push to GitHub only on Dheepak's yes
