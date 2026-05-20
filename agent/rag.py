"""
Capstone RAG tool — indexes the engagement document corpus and exposes
a search tool for the agent.
"""
from __future__ import annotations

from pathlib import Path

import os

import chromadb
import litellm

EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
EMBED_API_BASE = os.getenv("EMBED_API_BASE") or None


def _embed(texts: list[str]) -> list[list[float]]:
    kwargs: dict = dict(model=EMBED_MODEL, input=texts)
    if EMBED_API_BASE:
        kwargs["api_base"] = EMBED_API_BASE
    resp = litellm.embedding(**kwargs)
    return [item["embedding"] for item in resp["data"]]


def _chunk(text: str, size: int = 400, overlap: int = 50) -> list[str]:
    chunks, start = [], 0
    while start < len(text):
        end = start + size
        chunk = text[start:end]
        if end < len(text) and not text[end].isspace():
            ls = chunk.rfind(" ")
            if ls > 0:
                end, chunk = start + ls, text[start : start + ls]
        chunks.append(chunk.strip())
        start = end - overlap
    return [c for c in chunks if c]


class RAGIndex:
    def __init__(self, docs_dir: Path):
        self._client = chromadb.Client()
        self._col = self._client.create_collection("rag_capstone", metadata={"hnsw:space": "cosine"})
        self._index(docs_dir)

    def _index(self, docs_dir: Path) -> None:
        chunks = []
        for path in docs_dir.glob("*.md"):
            for i, chunk in enumerate(_chunk(path.read_text())):
                chunks.append({"id": f"{path.name}_{i}", "text": chunk, "source": path.name})
        if not chunks:
            return
        for i in range(0, len(chunks), 50):
            batch = chunks[i : i + 50]
            self._col.add(
                ids=[c["id"] for c in batch],
                documents=[c["text"] for c in batch],
                embeddings=_embed([c["text"] for c in batch]),
                metadatas=[{"source": c["source"]} for c in batch],
            )

    def search(self, query: str, k: int = 4) -> str:
        if self._col.count() == 0:
            return "No documents indexed."
        results = self._col.query(
            query_embeddings=_embed([query]),
            n_results=min(k, self._col.count()),
            include=["documents", "metadatas"],
        )
        return "\n---\n".join(
            f"[{results['metadatas'][0][i]['source']}]\n{results['documents'][0][i]}"
            for i in range(len(results["documents"][0]))
        )
