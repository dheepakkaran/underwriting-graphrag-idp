"""In-process smoke test of the FastAPI app on the real run outputs (results/). Writes results/api_smoke.txt."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
from fastapi.testclient import TestClient  # noqa: E402

import app.main as m  # noqa: E402

c = TestClient(m.app)
T = [json.loads(l) for l in (ROOT / "data/truth.jsonl").read_text().splitlines()]
ring = [t for t in T if "ring" in t["issues"]]
out = [f"GET /health -> {c.get('/health').json()}"]
q = c.get("/queue").json()
out.append(f"GET /queue -> {len(q)} referred files waiting for a human")
out.append(f"GET /files/{q[0]['file_id']}/flags -> {json.dumps(c.get(f'/files/{q[0]['file_id']}/flags').json())[:240]}")
a = c.post("/ask", json={"question": f"Which other applicants use the same mailing address as {ring[0]['applicant']}?"}).json()
out.append(f"POST /ask (ring question) -> {sorted(a['answer']['names'])}")
out.append(f"truth -> {sorted(t['applicant'] for t in ring[1:])}")
(ROOT / "results/api_smoke.txt").write_text("\n".join(out) + "\n")
print("\n".join(out))
