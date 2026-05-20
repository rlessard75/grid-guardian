#!/usr/bin/env python3
"""
Run all three PR fixtures end-to-end and write review JSONs.
Produces content the dashboard can display on first open.

Usage:
    python run_all_fixtures.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT.parent / ".env")

from agent.orchestrator import run_review  # noqa: E402

FIXTURES = [
    ROOT / "fixtures" / "pull_requests" / "pr_clean.json",
    ROOT / "fixtures" / "pull_requests" / "pr_secret_leak.json",
    ROOT / "fixtures" / "pull_requests" / "pr_risky_pattern.json",
]


def _progress(pr_id: str):
    def cb(phase: str, message: str) -> None:
        print(f"  [{pr_id}] [{phase.upper():12s}] {message}")
    return cb


def main() -> None:
    results = []
    for fixture_path in FIXTURES:
        pr_fixture = json.loads(fixture_path.read_text())
        pr_id = pr_fixture["pr_id"]
        print(f"\n{'─'*60}")
        print(f"  Running: {pr_id} — {pr_fixture.get('title', '')}")
        print(f"{'─'*60}")
        try:
            review = run_review(pr_fixture, progress_cb=_progress(pr_id))
            results.append((pr_id, review["status"], "ok"))
        except Exception as exc:
            print(f"  ERROR: {exc}")
            results.append((pr_id, "error", str(exc)))

    print(f"\n{'='*60}")
    print("  Summary")
    print(f"{'='*60}")
    for pr_id, status, note in results:
        print(f"  {pr_id:12s}  status={status}  {note}")
    print(f"{'='*60}\n")

    all_ok = all(note == "ok" for _, _, note in results)
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
