"""
Lessons-learned post-mortem search tool.

Primary: keyword scoring against document text (reliable, no API key needed).
Fallback: ChromaDB vector search if EMBED_MODEL and OpenAI key are available
(same pattern as agent/rag.py).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

LESSONS_DIR = (
    Path(__file__).parent.parent / "fixtures" / "lessons_learned"
)
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
EMBED_API_BASE = os.getenv("EMBED_API_BASE") or None

# Stop words to ignore in keyword scoring
_STOP = {
    "a", "an", "the", "in", "on", "for", "of", "to", "and", "or",
    "is", "are", "was", "were", "be", "been", "by", "at", "from",
    "this", "that", "with", "as", "it", "its",
}


def query_lessons_learned(query_text: str, k: int = 3) -> str:
    """
    Return the top-k post-mortems most relevant to query_text.
    Uses keyword scoring; falls back to vector search if embeddings available.
    """
    # Try vector search first (same pattern as rag.py)
    try:
        result = _vector_search(query_text, k)
        if result:
            return result
    except Exception:
        pass

    return _keyword_search(query_text, k)


def _keyword_search(query_text: str, k: int) -> str:
    """Score documents by how many query words appear in their text."""
    query_words = {w.lower() for w in query_text.split()} - _STOP

    scores: list[tuple[int, str, str]] = []
    for path in LESSONS_DIR.glob("*.md"):
        text = path.read_text()
        text_lower = text.lower()
        score = sum(1 for w in query_words if w in text_lower)
        scores.append((score, path.name, text))

    scores.sort(key=lambda x: x[0], reverse=True)
    results = [s for s in scores if s[0] > 0][:k]

    if not results:
        return json.dumps({"matches": [], "count": 0, "note": "No matching post-mortems found."})

    return "\n---\n".join(f"[{name}]\n{text}" for _, name, text in results)


def _vector_search(query_text: str, k: int) -> str:
    """ChromaDB vector search — identical pattern to agent/rag.py."""
    import chromadb
    import litellm

    def embed(texts: list[str]) -> list:
        kwargs: dict = dict(model=EMBED_MODEL, input=texts)
        if EMBED_API_BASE:
            kwargs["api_base"] = EMBED_API_BASE
        resp = litellm.embedding(**kwargs)
        return [item["embedding"] for item in resp["data"]]

    client = chromadb.Client()
    col = client.create_collection("ll_search", metadata={"hnsw:space": "cosine"})

    docs = []
    for path in LESSONS_DIR.glob("*.md"):
        docs.append({"id": path.name, "text": path.read_text(), "source": path.name})

    if not docs:
        return ""

    col.add(
        ids=[d["id"] for d in docs],
        documents=[d["text"] for d in docs],
        embeddings=embed([d["text"] for d in docs]),
        metadatas=[{"source": d["source"]} for d in docs],
    )

    results = col.query(
        query_embeddings=embed([query_text]),
        n_results=min(k, col.count()),
        include=["documents", "metadatas"],
    )
    return "\n---\n".join(
        f"[{results['metadatas'][0][i]['source']}]\n{results['documents'][0][i]}"
        for i in range(len(results["documents"][0]))
    )
