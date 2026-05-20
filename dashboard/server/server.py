"""
Thin FastAPI server — wires the React dashboard to the PR Governance Agent.

Endpoints:
  POST /api/reviews              run a review (non-blocking, returns {pr_id, status})
  GET  /api/reviews              list all completed review summaries
  GET  /api/reviews/{pr_id}      get a single review (or running status)
  GET  /api/reviews/{pr_id}/stream  SSE progress stream
  POST /api/decisions            record approve / request-changes decision

Run with:
  cd dashboard/server
  uvicorn server:app --reload --port 8000
"""
from __future__ import annotations

import asyncio
import json
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

# Ensure project root is importable
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT.parent / ".env")

from agent.orchestrator import run_review  # noqa: E402

REVIEWS_DIR = ROOT / "output" / "reviews"
DECISIONS_DIR = ROOT / "output" / "decisions"
REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
DECISIONS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="PR Governance Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory progress store: pr_id → list[{phase, message}]
_progress: dict[str, list] = {}


# ── Review endpoints ───────────────────────────────────────────────────────


@app.post("/api/reviews")
async def create_review(body: dict) -> dict:
    """
    Start a PR governance review in a background thread.
    Returns immediately with {pr_id, status: 'running'}.
    Poll GET /api/reviews/{pr_id} or stream GET /api/reviews/{pr_id}/stream for results.
    """
    pr_id = body.get("pr_id") or f"PR-UPLOAD-{int(time.time() * 1000)}"
    body["pr_id"] = pr_id
    _progress[pr_id] = []

    def _run() -> None:
        def cb(phase: str, message: str) -> None:
            _progress[pr_id].append({"phase": phase, "message": message})

        try:
            run_review(body, progress_cb=cb)
        except Exception as exc:
            _progress[pr_id].append({"phase": "error", "message": str(exc)})
        finally:
            _progress[pr_id].append({"phase": "complete", "pr_id": pr_id})

    threading.Thread(target=_run, daemon=True).start()
    return {"pr_id": pr_id, "status": "running"}


@app.get("/api/reviews")
async def list_reviews() -> list:
    """List all completed review summaries, most recent first."""
    reviews = []
    for path in sorted(REVIEWS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(path.read_text())
            pr_data = data.get("context_snapshot", {}).get("pr_data", {})
            reviews.append({
                "pr_id": data.get("pr_id"),
                "status": data.get("status"),
                "title": pr_data.get("title", ""),
                "author": pr_data.get("author", ""),
                "branch": pr_data.get("branch", ""),
                "created_at": pr_data.get("created_at", ""),
                "governance_count": len(data.get("raw_findings", {}).get("governance", [])),
                "pattern_count": len(data.get("raw_findings", {}).get("patterns", [])),
            })
        except Exception:
            pass
    return reviews


@app.get("/api/reviews/{pr_id}/stream")
async def stream_review(pr_id: str) -> StreamingResponse:
    """
    SSE stream of progress events for a running review.
    Each event: data: {"phase": "...", "message": "..."}\n\n
    Terminal event: data: {"phase": "complete", "pr_id": "..."}\n\n
    """
    async def generate():
        sent = 0
        review_path = REVIEWS_DIR / f"{pr_id}.json"

        for _ in range(240):  # max ~2 min at 0.5 s intervals
            events = _progress.get(pr_id, [])

            # Flush any new events
            while sent < len(events):
                event = events[sent]
                yield f"data: {json.dumps(event)}\n\n"
                sent += 1
                if event.get("phase") == "complete":
                    return

            # If no more events but the review file exists, we're done
            if review_path.exists() and pr_id not in _progress:
                yield f"data: {json.dumps({'phase': 'complete', 'pr_id': pr_id})}\n\n"
                return

            await asyncio.sleep(0.5)

        yield f"data: {json.dumps({'phase': 'error', 'message': 'Stream timeout'})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/reviews/{pr_id}")
async def get_review(pr_id: str) -> dict:
    """Get a completed review JSON, or current running status."""
    path = REVIEWS_DIR / f"{pr_id}.json"
    if path.exists():
        return json.loads(path.read_text())
    if pr_id in _progress:
        return {
            "pr_id": pr_id,
            "status": "running",
            "progress": _progress[pr_id],
        }
    raise HTTPException(status_code=404, detail=f"Review '{pr_id}' not found")


# ── Decision endpoint ──────────────────────────────────────────────────────


@app.post("/api/decisions")
async def create_decision(body: dict) -> dict:
    """Record an approve or request-changes decision."""
    pr_id = body.get("pr_id")
    if not pr_id:
        raise HTTPException(status_code=400, detail="pr_id is required")

    decision = {
        "pr_id": pr_id,
        "decision": body.get("decision", "unknown"),  # "approved" | "changes_requested"
        "reviewer": body.get("reviewer", "reviewer"),
        "comment": body.get("comment", ""),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    path = DECISIONS_DIR / f"{pr_id}.json"
    path.write_text(json.dumps(decision, indent=2))
    return decision


@app.get("/api/decisions/{pr_id}")
async def get_decision(pr_id: str) -> dict:
    """Get the decision for a PR, if one exists."""
    path = DECISIONS_DIR / f"{pr_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="No decision recorded")
    return json.loads(path.read_text())


# ── Health check ───────────────────────────────────────────────────────────


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "reviews_dir": str(REVIEWS_DIR)}


# ── Serve Vite build in production ─────────────────────────────────────────
# Must be mounted last so API routes take precedence.
DIST = ROOT / "dashboard" / "dist"
if DIST.exists():
    app.mount("/", StaticFiles(directory=DIST, html=True), name="spa")
