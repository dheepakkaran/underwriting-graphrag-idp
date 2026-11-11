import json

import pytest
from conftest import ROOT, truth_extraction
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch, truth):
    import app.main as m
    res = tmp_path / "results"
    res.mkdir()
    fids = sorted(truth)[:4]
    (res / "extract_v2_all.jsonl").write_text("\n".join(
        json.dumps({"file_id": f, "extraction": truth_extraction(truth[f])}) for f in fids) + "\n")
    files = [{"file_id": f, "route": "refer" if i % 2 == 0 else "standard",
              "flags": [{"code": "sqft_mismatch", "detail": "d", "quote": "q"}] if i % 2 == 0 else []}
             for i, f in enumerate(fids)]
    (res / "triage_test.json").write_text(json.dumps({"files": files}))
    monkeypatch.setattr(m, "RES", res)
    monkeypatch.setattr(m, "LOG", res / "review_log.jsonl")
    return TestClient(m.app), fids


def test_health_and_files(client):
    c, fids = client
    assert c.get("/health").json() == {"ok": True, "files": 4, "triaged": 4}
    assert len(c.get("/files").json()) == 4


def test_queue_holds_only_referred_files_and_logs_decisions(client):
    c, fids = client
    q = c.get("/queue").json()
    assert [x["file_id"] for x in q] == [fids[0], fids[2]]
    r = c.post(f"/queue/{fids[0]}/decision", json={"decision": "override_to_standard", "reason": "inspection re-done", "reviewer": "uw1"})
    assert r.status_code == 200
    assert [x["file_id"] for x in c.get("/queue").json()] == [fids[2]]


def test_decision_needs_reason_and_valid_choice(client):
    c, fids = client
    assert c.post(f"/queue/{fids[2]}/decision", json={"decision": "decline", "reason": "x", "reviewer": "u"}).status_code == 422
    assert c.post(f"/queue/{fids[2]}/decision", json={"decision": "approve_refer", "reason": "", "reviewer": "u"}).status_code == 422
    assert c.post(f"/queue/{fids[1]}/decision", json={"decision": "approve_refer", "reason": "ok ok", "reviewer": "u"}).status_code == 400


def test_ui_served(client):
    c, _ = client
    assert "review queue" in c.get("/").text.lower()
