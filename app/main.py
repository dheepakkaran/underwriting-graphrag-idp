"""FastAPI backend + one-page review UI for the (fictional) Pine Harbor Mutual pre-check prototype.

Reads the measured run outputs in results/ (extractions + triage), serves a human review queue, and answers
cross-file questions with the graph retriever. Review decisions (approve / override + reason) are appended to
results/review_log.jsonl. Secrets come from the environment only.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from uw import graph as G  # noqa: E402

RES = ROOT / "results"
LOG = RES / "review_log.jsonl"
app = FastAPI(title="Underwriting pre-check (fictional insurer, synthetic data)")


def _triage() -> dict[str, dict]:
    out = {}
    for split in ("dev", "test"):
        p = RES / f"triage_{split}.json"
        if p.exists():
            for f in json.loads(p.read_text())["files"]:
                out[f["file_id"]] = f
    return out


def _extractions() -> dict[str, dict]:
    p = RES / "extract_v2_all.jsonl"
    return G.load_extractions(p) if p.exists() else {}


def _decisions() -> dict[str, dict]:
    d = {}
    if LOG.exists():
        for r in map(json.loads, LOG.read_text().splitlines()):
            d[r["file_id"]] = r
    return d


class Decision(BaseModel):
    decision: str = Field(pattern="^(approve_refer|override_to_standard)$")
    reason: str = Field(min_length=3)
    reviewer: str = Field(min_length=1)


class Ask(BaseModel):
    question: str = Field(min_length=5)


@app.get("/health")
def health():
    return {"ok": True, "files": len(_extractions()), "triaged": len(_triage())}


@app.get("/files")
def files():
    t, dec = _triage(), _decisions()
    return [{"file_id": fid, "applicant": ex["applicant"], "broker": ex["broker"],
             "route": t.get(fid, {}).get("route"), "flags": len(t.get(fid, {}).get("flags", [])),
             "decision": dec.get(fid, {}).get("decision")} for fid, ex in sorted(_extractions().items())]


@app.get("/files/{file_id}/flags")
def flags(file_id: str):
    t = _triage()
    if file_id not in t:
        raise HTTPException(404, "file not triaged")
    return {"file_id": file_id, "route": t[file_id]["route"], "flags": t[file_id]["flags"]}


@app.get("/queue")
def queue():
    dec = _decisions()
    return [{"file_id": fid, "flags": f["flags"]} for fid, f in sorted(_triage().items())
            if f["route"] == "refer" and fid not in dec]


@app.post("/queue/{file_id}/decision")
def decide(file_id: str, d: Decision):
    if _triage().get(file_id, {}).get("route") != "refer":
        raise HTTPException(400, "only referred files are in the review queue")
    rec = {"file_id": file_id, **d.model_dump(), "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
    RES.mkdir(exist_ok=True)
    with LOG.open("a") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


@app.post("/ask")
def ask(a: Ask):
    from uw import rag
    g = G.build(_extractions())
    ctx = rag.graph_context(g, a.question)
    if not ctx:
        return {"answer": None, "note": "no applicant, broker or address from the question was found in the graph"}
    return {"answer": rag.answer("api_ask", a.question, ctx).model_dump(), "context": ctx}


@app.get("/")
def ui():
    return FileResponse(ROOT / "app" / "index.html")
