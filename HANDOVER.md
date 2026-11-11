# HANDOVER · Underwriting pre-check prototype (fictional insurer, synthetic data)

## What it does
For each submission (application + loss run + inspection PDF) it extracts the key fields with quotes, checks them against the other documents and the internal records, looks across all files for broker/address rings, and routes the file to **standard review** or **refer to a senior underwriter**. Referred files wait in a review queue; a human approves or overrides with a reason (logged). There is no decline route.

## Architecture
```
PDFs ──pdfplumber──► text ──Claude Haiku 5.5 (structured output, Pydantic)──► Extraction (+ verbatim quotes)
                                                                                     │
                     internal records (SQLite) ◄── validators (code) ◄───────────────┤
                                                                                     ▼
                          entity graph (networkx: applicant–broker–address–claim) ◄──┘
                                   │
LangGraph:  validate ─► investigate (Claude + tools: graph_neighbors, lookup_record, flag_discrepancy[ring]) ─► route (code)
                                                                                   └─ refer ─► interrupt() ─► human review queue
FastAPI: /health /files /files/{id}/flags /queue /queue/{id}/decision /ask   +  one-page review UI (app/index.html)
```
Design rules: the route is computed by code from flags, never chosen by the model; in-file checks are deterministic; the agent only adds the cross-file `ring` flag and only when the graph supports it; document text is data (3 planted instructions changed 0 routes).

## Run
```bash
uv sync                                  # Python 3.12
cp .env.example .env                     # ANTHROPIC_API_KEY=... (only for LLM steps and /ask)
python data/gen.py                       # regenerate the 60 synthetic files (seed 7)
python eval/run_baseline.py              # frozen rules baseline
python eval/run_extract.py all v2        # extraction
python eval/run_rag.py test              # vector RAG vs graph retrieval
python eval/run_triage.py test           # agent triage
python eval/make_results.py              # RESULTS.md
python -m pytest -q                      # 14 tests, offline
uvicorn app.main:app --port 8000         # review UI at http://localhost:8000
docker compose up --build                # same, containerised (key from .env, never baked in)
./docker_smoke.sh                        # build + start + check /health, /queue, / + stop
```

## Known limits
- Synthetic, born-digital PDFs in three layouts; no OCR, no scanned or handwritten files.
- Graph entity linking is exact string match on names / addresses; real data needs fuzzy matching and address normalisation.
- One extraction error on test (a number disagreeing with its own quote) caused a false refer; see FAILURES.md #5.
- Docker: image built and smoke-tested locally (`docker_smoke.sh` → `results/docker_smoke.txt`); no cloud deploy.

## Next steps
1. Re-parse numeric fields from their quotes; disagreement → "extraction uncertain", not a risk flag.
2. Fuzzy entity resolution (addresses, business name variants) before the graph.
3. Shadow-mode pilot: run beside underwriters for two weeks and measure agreement and minutes saved per file.
4. Governance: model inventory, override-rate monitoring, documented human oversight, in line with the NAIC Model Bulletin on the Use of AI Systems by Insurers (Dec 2023).
