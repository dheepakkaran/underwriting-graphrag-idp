"""Vector RAG vs GraphRAG-style retrieval on the frozen multi-hop questions. Same answer prompt + schema.
The graph is built from the LLM extractions of all 60 files (results/extract_v2_all.jsonl), never from truth.
Usage: python eval/run_rag.py dev | test     -> results/rag_vs_graphrag_<split>.json (paired bootstrap 95% CI)"""
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
from eval.score import SPLIT  # noqa: E402
from uw import graph as G  # noqa: E402
from uw import llm, rag  # noqa: E402

split = sys.argv[1]
Q = [q for q in map(json.loads, (ROOT / "eval/questions.jsonl").read_text().splitlines()) if q["split"] == split]
ex = G.load_extractions(ROOT / "results/extract_v2_all.jsonl")
g = G.build(ex)
vi = rag.VectorIndex(SPLIT["dev"] + SPLIT["test"])


def correct(q, a):
    n = lambda xs: sorted(x.strip().lower() for x in xs)
    if q["type"] == "shared_mailing":
        return n(a.names) == n(q["names"])
    if q["type"] == "location_to_broker_claims":
        return n(a.names)[:1] == n(q["names"]) and a.number == q["number"]
    return a.number == q["number"]


rows, s0 = [], llm.spent_usd()
for q in Q:
    r = {"id": q["id"], "type": q["type"]}
    for arm, ctx in (("vector", "\n\n".join(vi.retrieve(q["q"]))), ("graph", rag.graph_context(g, q["q"]))):
        a = rag.answer(f"rag_{arm}:{q['id']}", q["q"], ctx or "(no context found)")
        r[arm] = correct(q, a)
        r[f"{arm}_answer"] = a.model_dump()
    r["graph_seeds"] = G.link(g, q["q"])
    rows.append(r)
    print(q["id"], q["type"], "vector", r["vector"], "graph", r["graph"], flush=True)

v = [r["vector"] for r in rows]
gr = [r["graph"] for r in rows]
rng = random.Random(0)
diffs = []
for _ in range(10000):
    idx = [rng.randrange(len(rows)) for _ in rows]
    diffs.append(sum(gr[i] for i in idx) / len(idx) - sum(v[i] for i in idx) / len(idx))
diffs.sort()
by_type = {}
for r in rows:
    t = by_type.setdefault(r["type"], {"n": 0, "vector": 0, "graph": 0})
    t["n"] += 1; t["vector"] += r["vector"]; t["graph"] += r["graph"]
summ = dict(split=split, n=len(rows), vector_correct=sum(v), graph_correct=sum(gr),
            vector_acc=round(sum(v) / len(v), 3), graph_acc=round(sum(gr) / len(gr), 3),
            diff_graph_minus_vector=round((sum(gr) - sum(v)) / len(v), 3),
            ci95=[round(diffs[249], 3), round(diffs[9749], 3)], by_type=by_type, top_k=rag.TOP_K,
            usd=round(llm.spent_usd() - s0, 4), rows=rows)
(ROOT / f"results/rag_vs_graphrag_{split}.json").write_text(json.dumps(summ, indent=1))
print(json.dumps({k: summ[k] for k in summ if k != "rows"}, indent=1))
