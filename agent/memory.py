"""
Capstone memory layer — combines long-term and semantic memory from the Agent Memory notebook.
"""
from __future__ import annotations

import json
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


class Memory:
    """Unified memory: long-term (JSON) + semantic (ChromaDB)."""

    def __init__(self, memory_file: Path):
        self.memory_file = memory_file
        self._lt: dict = {}
        if memory_file.exists() and memory_file.stat().st_size > 2:
            self._lt = json.loads(memory_file.read_text())

        self._chroma = chromadb.Client()
        self._sem = self._chroma.get_or_create_collection("semantic", metadata={"hnsw:space": "cosine"})
        self._id = self._sem.count()

    # Long-term (key-value)

    def set(self, key: str, value: str) -> str:
        self._lt[key] = value
        self.memory_file.write_text(json.dumps(self._lt, indent=2))
        return f"Remembered: {key} = {value}"

    def get(self, key: str) -> str | None:
        return self._lt.get(key)

    def all_facts(self) -> dict:
        return dict(self._lt)

    # Semantic (vector)

    def remember_fact(self, fact: str) -> str:
        self._id += 1
        self._sem.add(ids=[str(self._id)], documents=[fact], embeddings=_embed([fact]))
        return f"Stored fact: {fact[:80]}"

    def recall(self, query: str, k: int = 3) -> list[str]:
        if self._sem.count() == 0:
            return []
        results = self._sem.query(
            query_embeddings=_embed([query]),
            n_results=min(k, self._sem.count()),
            include=["documents"],
        )
        return results["documents"][0]

    def context_for(self, query: str) -> str:
        """Build a context string to inject into the system prompt."""
        parts = []
        if self._lt:
            parts.append("Known facts:\n" + "\n".join(f"- {k}: {v}" for k, v in self._lt.items()))
        recalled = self.recall(query)
        if recalled:
            parts.append("Relevant memories:\n" + "\n".join(f"- {r}" for r in recalled))
        return "\n\n".join(parts) if parts else ""
