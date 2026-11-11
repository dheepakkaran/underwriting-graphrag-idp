"""LLM extraction on one split with one prompt version. Writes results/extract_<ver>_<split>.jsonl + summary json.
Usage: python eval/run_extract.py dev v1 | test v2 | all v2"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
from eval.score import SPLIT, field_accuracy, field_hits  # noqa: E402
from uw import idp, llm  # noqa: E402

split, ver = sys.argv[1], sys.argv[2]
ids = SPLIT["dev"] + SPLIT["test"] if split == "all" else SPLIT[split]
rows, out, t0, s0 = [], [], time.time(), llm.spent_usd()
for fid in ids:
    try:
        ex = idp.extract_llm(fid, ver).model_dump()
        rows.append((fid, ex))
        out.append({"file_id": fid, "extraction": ex, "hits": field_hits(fid, ex)})
    except llm.BudgetExceeded:
        raise
    except Exception as e:  # keep going; a failed file counts as all-wrong
        out.append({"file_id": fid, "extraction": None, "error": str(e)[:300]})
        rows.append((fid, {}))
    print(fid, "ok" if out[-1].get("extraction") else out[-1]["error"][:80], flush=True)
idp.save(ROOT / f"results/extract_{ver}_{split}.jsonl", out)
acc, n = field_accuracy(rows)
miss = {}
for r in out:
    for k, v in (r.get("hits") or {}).items():
        miss[k] = miss.get(k, 0) + (not v)
summ = dict(split=split, prompt=ver, files=len(ids), field_accuracy=round(acc, 3), fields_scored=n,
            misses_by_field=miss, errors=sum(1 for r in out if not r.get("extraction")),
            seconds_per_file=round((time.time() - t0) / len(ids), 2), usd=round(llm.spent_usd() - s0, 4))
(ROOT / f"results/extract_{ver}_{split}.json").write_text(json.dumps(summ, indent=1))
print(json.dumps(summ, indent=1))
