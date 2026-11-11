# Demo script (5 minutes)

1. **The problem (30 s).** Open `docs/01-client-brief.md`: three PDFs per file, mismatches inside a file, rings across files, a human must decide.
2. **One file (60 s).** Open `data/docs/PHM-1001/` PDFs. Then `/files/PHM-1001/flags` in the UI: the ring flag names the shared PO box, the broker and the other four applicants.
3. **Review queue (60 s).** Pick a referred file, read the quoted evidence, override one with a reason. Show `results/review_log.jsonl` got the decision.
4. **Ask across files (60 s).** In the UI: "What is the total paid amount on the loss runs of all applicants placed by Coastline Risk Partners?" Explain why plain vector search fails this (loss runs never name the broker) and the graph does not (RESULTS.md §3).
5. **Numbers and failures (90 s).** RESULTS.md: rules baseline vs agent, vector vs graph, $ cost. FAILURES.md #3–#5: the agent over-flagging, why in-file checks moved to code, the one test false refer.
