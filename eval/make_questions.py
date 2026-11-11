"""30 multi-hop questions with answers computed from data/truth.jsonl (seeded). 10 dev / 20 test, frozen.
Types: shared_mailing (address hop), broker_total_paid (broker -> applicants -> claims),
broker_fire_count (broker -> applicants -> claim cause), location_to_broker_claims (address -> applicant -> broker + claims)."""
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
T = [json.loads(l) for l in (ROOT / "data/truth.jsonl").read_text().splitlines()]
rng = random.Random(11)
by_broker, by_mail = defaultdict(list), defaultdict(list)
for t in T:
    by_broker[t["broker"]].append(t)
    by_mail[t["mailing"]].append(t)

qs = []
ring = [t for t in T if "ring" in t["issues"]]
others = rng.sample([t for t in T if "ring" not in t["issues"]], 4)
for t in ring + others:   # 9
    names = sorted(o["applicant"] for o in by_mail[t["mailing"]] if o["file_id"] != t["file_id"])
    qs.append(dict(type="shared_mailing", q=f"Which other applicants use the same mailing address as {t['applicant']}?",
                   names=names, number=None))
for b in sorted(by_broker):   # 8
    qs.append(dict(type="broker_total_paid", q=f"What is the total paid amount on the loss runs of all applicants placed by {b}?",
                   names=[], number=sum(c["amount"] for t in by_broker[b] for c in t["claims"])))
for b in sorted(by_broker):   # 8
    qs.append(dict(type="broker_fire_count", q=f"How many applicants placed by {b} have at least one fire claim on their loss run?",
                   names=[], number=sum(any(c["cause"] == "fire" for c in t["claims"]) for t in by_broker[b])))
for t in rng.sample(T, 5):    # 5
    qs.append(dict(type="location_to_broker_claims",
                   q=f"Which broker placed the applicant whose building is at {t['location']}, and how many claims are on that applicant's loss run?",
                   names=[t["broker"]], number=len(t["claims"])))
rng.shuffle(qs)
for i, q in enumerate(qs):
    q["id"], q["split"] = f"Q{i + 1:02d}", "dev" if i < 10 else "test"
(ROOT / "eval/questions.jsonl").write_text("\n".join(json.dumps(q) for q in qs) + "\n")
print(len(qs), "questions;", sum(q["split"] == "test" for q in qs), "test")
