# Sprint log (solo, time-boxed mini sprints; labelled as practice, not a real team)

**Sprint 1 · discover + data + baseline.** Goal: scoped problem and a baseline to beat. Done: brief, 3 simulated interviews, scope + metrics, seeded generator (60 files, 28 planted risks, 3 injections), rules baseline; found and fixed a too-weak regex before freezing it.
Stand-up: blocked on an invalid API key; built everything that needs no LLM meanwhile.

**Sprint 2 · LLM pipeline on dev.** Goal: extraction + RAG + agent working on 20 dev files. Done: extraction v1 → v2 (verbatim quotes), vector vs graph retrieval on dev, agent iterations 1 → 3 (evidence guardrail, then in-file checks moved to code). Froze prompt and agent.
Stand-up: agent over-flagged a clean file twice; fixed by narrowing its job, not by more prompting.

**Sprint 3 · test once + ship.** Goal: frozen test run, app, handover. Done: test runs (extraction, RAG vs graph, triage), FastAPI + review UI, in-process API smoke, Dockerfile, 14 tests, RESULTS / FAILURES / HANDOVER / demo script.
Stand-up: Docker smoke waits for Docker install; one test false refer documented.
