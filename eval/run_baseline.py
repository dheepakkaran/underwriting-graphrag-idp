"""Rules baseline (no LLM): regex extraction + the same validators. Frozen before any LLM run.
Writes results/baseline_rules.json."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
from eval.score import SPLIT, field_accuracy, routing  # noqa: E402
from uw import idp, validate  # noqa: E402

out = {}
for split in ("dev", "test"):
    ids = SPLIT[split]
    rows, pred = [], {}
    for fid in ids:
        ex = idp.extract_regex(fid)
        rows.append((fid, ex))
        pred[fid] = validate.route_from(validate.check(fid, ex))
    acc, n = field_accuracy(rows)
    out[split] = dict(field_accuracy=round(acc, 3), fields_scored=n, routing=routing(pred, ids))
(ROOT / "results").mkdir(exist_ok=True)
(ROOT / "results/baseline_rules.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
