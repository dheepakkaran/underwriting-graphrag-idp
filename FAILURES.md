# FAILURES · what broke and what was done next

1. **Rules baseline was weaker than it should be (fixed before freezing).** The first regex read only the square footage from the one-row table form, so the baseline missed sprinkler and claims fields there (dev recall 18%, test 24%). A weak baseline makes the LLM look better than it is, so the regex was completed for both known forms before any LLM run. Frozen baseline: test recall 64.7%. The prose form is deliberately left unread ("a new broker format").

2. **Extraction quotes were paraphrased (prompt v1 → v2, dev only).** For the table form the model wrote quotes like `Sprinklered column: No`, which appear nowhere in the document (dev: 96/100 verbatim). v2 adds: copy the row text character for character. Dev 98/100, test 200/200.

3. **The agent over-flagged a clean file (agent iteration 1 → 2, dev only).** PHM-1021 is clean, but the agent flagged a sprinkler mismatch and undisclosed claims, quoting a table header word (`"Sprinklered"`) and its own field summary as "evidence". Fix 2: the `flag_discrepancy` tool rejects in-file flags whose evidence is not verbatim document text, and ring flags the graph does not support.

4. **Grounded evidence, wrong logic (iteration 2 → 3, dev only).** After fix 2 the agent still flagged PHM-1021, now quoting a real inspection sentence ("No automatic sprinkler system was found on site") while claiming the application said sprinklered (the extraction said it did not). Verbatim checks cannot catch a wrong inference. Fix 3: in-file checks belong to deterministic validators; the agent may only add the cross-file `ring` flag, the one thing code cannot see from a single file. Dev 20/20 after this, then the agent was frozen.

5. **Test false refer: an extraction number disagreed with its own quote.** PHM-1051 discloses 1 prior claim; the model extracted `prior_claims_disclosed = 0` while quoting the row `1933 17,500 wood frame No 1 $1,000,000`. The validator then flagged "undisclosed claims". A reviewer sees the quote and overrides in seconds, but it is a real error. Next step: re-parse numeric fields from their own quote and flag disagreements as "extraction uncertain" instead of a risk.

6. **A graph answer was right but scored wrong.** Test Q23 asked for the broker of a location; the graph arm answered the right broker and claim count but also listed the applicant's name in `names`, which the frozen scorer reads as a wrong first name. Kept as wrong (19/20); the scorer was not changed after seeing test results.

7. **Vector RAG cannot do aggregation (expected, measured).** Broker totals need 6–10 loss runs, and loss runs never name the broker, so top-8 chunks cannot connect them: vector RAG 0/8 on broker totals vs graph 8/8. Vector RAG did fine on single-file lookups (location questions 2/2).

8. **Synthetic PDFs are easy for extraction.** Clean, born-digital text with three layouts: 99.7% field accuracy here says little about scanned or handwritten submissions. The extraction number is a pipeline check, not a claim about real documents.

9. **Local HTTP smoke blocked inside the coding session; Docker run by hand.** The sandbox blocks `curl localhost`, so the API smoke first ran in-process with FastAPI's TestClient (`results/api_smoke.txt`). The first image build would also have failed: `uv export` listed the project itself as a requirement, and the build context would have shipped `.venv` and `.env`. Fixed with `--no-emit-project` and a `.dockerignore`, then `docker_smoke.sh` built and ran the container on 2026-11-11: `/health` 60 files, `/queue` 29 referred, UI 200 (`results/docker_smoke.txt`).
