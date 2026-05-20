#!/usr/bin/env python3
"""
CLI entry point: run a PR governance review on a fixture file.

Usage:
    python run_review.py fixtures/pull_requests/pr_clean.json
    python run_review.py fixtures/pull_requests/pr_secret_leak.json
    python run_review.py fixtures/pull_requests/pr_risky_pattern.json
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


def _progress(phase: str, message: str) -> None:
    print(f"  [{phase.upper():12s}] {message}")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python run_review.py <pr_fixture.json>\n")
        print("Available fixtures:")
        for p in sorted((ROOT / "fixtures" / "pull_requests").glob("*.json")):
            print(f"  {p.relative_to(ROOT)}")
        sys.exit(1)

    fixture_path = Path(sys.argv[1])
    if not fixture_path.is_absolute():
        fixture_path = ROOT / fixture_path
    if not fixture_path.exists():
        print(f"Error: {fixture_path} not found")
        sys.exit(1)

    pr_fixture = json.loads(fixture_path.read_text())

    print(f"\n{'='*60}")
    print(f"  PR: {pr_fixture['pr_id']} — {pr_fixture.get('title', '')}")
    print(f"{'='*60}")

    review = run_review(pr_fixture, progress_cb=_progress)

    print(f"\n{'='*60}")
    print(f"  Status    : {review['status'].upper()}")
    print(f"  Governance: {len(review['raw_findings']['governance'])} finding(s)")
    print(f"  Patterns  : {len(review['raw_findings']['patterns'])} finding(s)")

    output_path = ROOT / "output" / "reviews" / f"{pr_fixture['pr_id']}.json"
    print(f"  Output    : {output_path}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
