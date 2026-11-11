"""Vector RAG baseline vs GraphRAG-style retrieval, same answer prompt and schema.

Vector: every document (application / loss run / inspection of every file) is one chunk; bge-small-en-v1.5
embeddings (fastembed, local, $0); top-k cosine. Graph: link entities in the question -> 2-hop neighbourhood -> facts.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from pydantic import BaseModel, Field

from uw import graph as G
from uw import idp

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "results" / "_emb_cache.npz"
TOP_K = 8


class Answer(BaseModel):
    names: list[str] = Field(description="applicant or broker names that answer the question; empty if none")
    number: int | None = Field(description="the numeric answer if the question asks for a count or a dollar total")
    reasoning: str = Field(description="one short sentence")


SYSTEM = ("Answer the question using ONLY the context. If the context does not contain enough to answer, give your "
          "best answer from what is there. Dollar totals as whole dollars. Names exactly as written in the context.")


class VectorIndex:
    def __init__(self, file_ids: list[str]):
        from fastembed import TextEmbedding
        self.model = TextEmbedding("BAAI/bge-small-en-v1.5", cache_dir=str(ROOT / ".cache" / "fastembed"))
        self.chunks = []
        for fid in file_ids:
            for kind, text in idp.doc_text(fid).items():
                self.chunks.append(f"[{fid} {kind}]\n{text}")
        if CACHE.exists() and int(np.load(CACHE)["n"]) == len(self.chunks):
            self.emb = np.load(CACHE)["emb"]
        else:
            self.emb = np.array(list(self.model.embed(self.chunks)))
            np.savez(CACHE, emb=self.emb, n=len(self.chunks))
        self.emb /= np.linalg.norm(self.emb, axis=1, keepdims=True)

    def retrieve(self, q: str, k: int = TOP_K) -> list[str]:
        qe = np.array(list(self.model.query_embed(q)))[0]
        qe /= np.linalg.norm(qe)
        return [self.chunks[i] for i in np.argsort(-(self.emb @ qe))[:k]]


def answer(tag: str, question: str, context: str) -> Answer:
    from uw import llm
    return llm.parse(tag, SYSTEM, f"<context>\n{context}\n</context>\n\nQuestion: {question}", Answer, max_tokens=2000)


def graph_context(g, question: str) -> str:
    seeds = G.link(g, question)
    return G.facts(g, G.neighbourhood(g, seeds, hops=2)) if seeds else ""
