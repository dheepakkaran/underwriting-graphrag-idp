"""Agent triage on one split: LangGraph (validate -> investigate with tools -> route -> human review interrupt).
Uses the v2 LLM extractions. A file that reaches interrupt() = 'refer' (queued for a human). Compared with the
frozen rules baseline. Usage: python eval/run_triage.py dev | test  -> results/triage_<split>.json"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
from eval.score import SPLIT, TRUTH, routing  # noqa: E402
from uw import agent, idp, llm  # noqa: E402
from uw import graph as G  # noqa: E402

split = sys.argv[1]
ids = SPLIT[split]
ex = G.load_extractions(ROOT / "results/extract_v2_all.jsonl")
app = agent.make(G.build(ex))
pred, files, s0, t0 = {}, [], llm.spent_usd(), time.time()
for fid in ids:
    cfg = {"configurable": {"thread_id": f"{split}-{fid}"}}
    st = app.invoke({"file_id": fid, "extraction": ex[fid], "texts": idp.doc_text(fid)}, cfg)
    queued = "__interrupt__" in st
    pred[fid] = st["route"]
    files.append({"file_id": fid, "route": st["route"], "queued_for_human": queued,
                  "flags": st["flags"], "truth_issues": TRUTH[fid]["issues"], "injected": TRUTH[fid]["injected"],
                  "notes": st.get("notes", "")})
    print(fid, st["route"], [f["code"] for f in st["flags"]], "truth", TRUTH[fid]["issues"], flush=True)
base = json.loads((ROOT / "results/baseline_rules.json").read_text())[split]["routing"]
flag_codes = [f["code"] for x in files for f in x["flags"]]
grounded = [f.get("quote_verified") for x in files for f in x["flags"] if "quote_verified" in f]
summ = dict(split=split, agent=routing(pred, ids), rules_baseline=base,
            decline_routes=sum(p not in ("standard", "refer") for p in pred.values()),
            agent_ring_flags=flag_codes.count("ring"),
            validator_quotes_verified=f"{sum(bool(x) for x in grounded)}/{len(grounded)}",
            seconds_per_file=round((time.time() - t0) / len(ids), 2), usd=round(llm.spent_usd() - s0, 4))
(ROOT / f"results/triage_{split}.json").write_text(json.dumps(summ | {"files": files}, indent=1))
print(json.dumps(summ, indent=1))
