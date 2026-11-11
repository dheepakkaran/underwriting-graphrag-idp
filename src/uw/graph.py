"""Entity graph built from the EXTRACTED fields (not from the hidden truth).

Nodes: applicant, broker, address (mailing + location), claim. Edges: applicant -placed_by-> broker,
applicant -mails_to-> address, applicant -located_at-> address, applicant -has_claim-> claim.
GraphRAG-style retrieval = link question entities to nodes -> 2-hop neighbourhood -> facts as text context.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[2]


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def build(extractions: dict[str, dict]) -> nx.Graph:
    g = nx.Graph()
    for fid, ex in extractions.items():
        a = f"applicant:{norm(ex['applicant'])}"
        g.add_node(a, kind="applicant", label=ex["applicant"], file_id=fid,
                   claims=len(ex.get("loss_run_claims") or []),
                   paid=sum(c.get("amount", 0) for c in ex.get("loss_run_claims") or []),
                   disclosed=ex.get("prior_claims_disclosed"))
        b = f"broker:{norm(ex['broker'])}"
        g.add_node(b, kind="broker", label=ex["broker"])
        g.add_edge(a, b, rel="placed_by")
        m = f"address:{norm(ex['mailing_address'])}"
        g.add_node(m, kind="address", label=ex["mailing_address"])
        g.add_edge(a, m, rel="mails_to")
        loc = f"address:{norm(ex['location_address'])}"
        if loc != m:
            g.add_node(loc, kind="address", label=ex["location_address"])
            g.add_edge(a, loc, rel="located_at")
        for k, c in enumerate(ex.get("loss_run_claims") or []):
            cn = f"claim:{fid}:{k}"
            g.add_node(cn, kind="claim", label=f"{c['cause']} on {c['date']}, paid ${c['amount']:,}",
                       cause=c["cause"], amount=c["amount"])
            g.add_edge(a, cn, rel="has_claim")
    return g


def link(g: nx.Graph, text: str) -> list[str]:
    """Entity linking by exact (normalised) label match inside the question."""
    t = norm(text)
    hits = [n for n, d in g.nodes(data=True) if d["kind"] in ("applicant", "broker", "address") and norm(d["label"]) in t]
    return sorted(hits, key=lambda n: -len(g.nodes[n]["label"]))


def neighbourhood(g: nx.Graph, seeds: list[str], hops: int = 2) -> list[str]:
    keep = set()
    for s in seeds:
        keep |= set(nx.single_source_shortest_path_length(g, s, cutoff=hops))
    return sorted(keep)


def facts(g: nx.Graph, nodes: list[str]) -> str:
    lines = []
    for n in nodes:
        d = g.nodes[n]
        if d["kind"] != "applicant":
            continue
        nb = {r: [g.nodes[x]["label"] for x in g.neighbors(n) if g.edges[n, x]["rel"] == r]
              for r in ("placed_by", "mails_to", "located_at", "has_claim")}
        lines.append(f"- {d['label']} (file {d['file_id']}): broker {', '.join(nb['placed_by'])}; mailing address "
                     f"{', '.join(nb['mails_to']) or 'same as location'}; location {', '.join(nb['located_at']) or ', '.join(nb['mails_to'])}; "
                     f"{d['claims']} claim(s) on the loss run, total paid ${d['paid']:,}"
                     + (f": {'; '.join(nb['has_claim'])}" if nb["has_claim"] else "") + f"; claims disclosed on application: {d['disclosed']}")
    return "\n".join(lines)


def shared_mailing(g: nx.Graph, applicant_node: str) -> list[dict]:
    """Other applicants that share this applicant's mailing address (used by the agent's graph tool)."""
    out = []
    for m in g.neighbors(applicant_node):
        if g.edges[applicant_node, m]["rel"] != "mails_to":
            continue
        for other in g.neighbors(m):
            if other != applicant_node and g.nodes[other]["kind"] == "applicant" and g.edges[m, other]["rel"] == "mails_to":
                od = g.nodes[other]
                brokers = [g.nodes[x]["label"] for x in g.neighbors(other) if g.edges[other, x]["rel"] == "placed_by"]
                out.append(dict(applicant=od["label"], file_id=od["file_id"], broker=brokers[0] if brokers else "",
                                claims=od["claims"], paid=od["paid"], shared_address=g.nodes[m]["label"]))
    return out


def load_extractions(path: Path) -> dict[str, dict]:
    return {r["file_id"]: r["extraction"] for r in map(json.loads, path.read_text().splitlines()) if r.get("extraction")}
