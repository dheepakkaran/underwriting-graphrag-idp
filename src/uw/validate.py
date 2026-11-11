"""Field validators: extracted fields vs the other documents in the file and vs internal records (SQLite).

Each flag = {code, detail, quote}. A flag's quote must appear verbatim in the documents (whitespace-normalised),
otherwise the flag is kept but marked quote_verified=False so a reviewer sees it was not grounded.
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data" / "records.sqlite"
SQFT_TOL = 0.85   # application below 85% of the measured / recorded area = understated


def record(file_id: str) -> dict:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    a = con.execute("SELECT * FROM applicants WHERE file_id=?", (file_id,)).fetchone()
    p = con.execute("SELECT * FROM property_records WHERE file_id=?", (file_id,)).fetchone()
    c = con.execute("SELECT date, cause, amount FROM claims WHERE file_id=?", (file_id,)).fetchall()
    con.close()
    return dict(applicant=dict(a) if a else {}, property=dict(p) if p else {}, claims=[dict(x) for x in c])


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip().lower()


def grounded(quote: str, texts: dict[str, str]) -> bool:
    q = _norm(quote)
    return bool(q) and any(q in _norm(t) for t in texts.values())


def check(file_id: str, ex: dict, texts: dict[str, str] | None = None) -> list[dict]:
    """ex = extraction as a dict (LLM Extraction.model_dump() or the regex baseline dict)."""
    rec = record(file_id)
    q = ex.get("quotes") or {}
    flags = []

    def add(code, detail, quote=""):
        f = {"code": code, "detail": detail, "quote": quote}
        if texts is not None and quote:
            f["quote_verified"] = grounded(quote, texts)
        flags.append(f)

    app, ins = ex.get("sqft_application"), ex.get("sqft_inspection")
    rec_sqft = rec["property"].get("square_feet")
    ref = max([v for v in (ins, rec_sqft) if v] or [0])
    if app and ref and app < SQFT_TOL * ref:
        add("sqft_mismatch", f"application {app:,} sq ft vs measured/recorded {ref:,} sq ft",
            q.get("sqft_application", "") or "")
    if ex.get("sprinklered_application") and (ex.get("sprinklered_inspection") is False
                                               or rec["property"].get("sprinklered") == 0):
        add("sprinkler_mismatch", "application says sprinklered; inspection / records say no sprinklers",
            q.get("sprinkler_inspection", "") or "")
    disclosed = ex.get("prior_claims_disclosed")
    listed = len(ex.get("loss_run_claims") or [])
    known = max(listed, len(rec["claims"]))
    if disclosed is not None and disclosed < known:
        add("undisclosed_claims", f"{disclosed} prior claims disclosed vs {known} on the loss run / in records",
            q.get("claims_disclosed", "") or "")
    for s in ex.get("instructions_found_in_documents") or []:
        add("embedded_instruction", "document contains instructions aimed at a reviewer (ignored)", s)
    return flags


RISK_CODES = {"sqft_mismatch", "sprinkler_mismatch", "undisclosed_claims", "ring"}


def route_from(flags: list[dict]) -> str:
    """Only two routes exist. There is no 'decline'."""
    return "refer" if any(f["code"] in RISK_CODES for f in flags) else "standard"
