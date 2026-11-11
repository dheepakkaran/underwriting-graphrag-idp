# 03 · Scoped problem

## Problem statement
For each new small-commercial submission (application + loss run + inspection report), pre-check the file against internal records and against every other file, explain each issue with a quote, and route the file to **standard review** or **refer to senior underwriter**. A human decides every file.

## Success metrics (measured on a frozen synthetic test split)
1. **Field extraction accuracy:** share of key fields extracted exactly right.
2. **Risky-file recall:** share of planted risky files routed to *refer* (miss = a risky file sent to standard review).
3. **Refer precision:** share of *refer* routes that are really risky (protects senior underwriters' time).
4. **Injection safety:** planted manipulation text changes 0 routes.
5. **Cross-file questions:** exact-match accuracy of graph retrieval vs a plain vector-RAG baseline on multi-hop questions.

## In scope
Synthetic PDFs, structured extraction, validators, entity graph, vector RAG baseline, graph retrieval, an agent with tools, a human review queue, a FastAPI backend + one-page review UI, Docker, tests, handover note.

## Out of scope
Real applicant data, pricing / premium, auto-decline, OCR of scanned images (text PDFs only), cloud deployment, Neo4j or the Microsoft GraphRAG library (a small hand-built graph retriever instead).

## Baselines (frozen before the LLM runs)
- **Rules baseline** for routing: deterministic validators only (no LLM), refer if any validator fires.
- **Vector RAG baseline** for questions: bge-small embeddings over document chunks, top-k, same answer prompt.
