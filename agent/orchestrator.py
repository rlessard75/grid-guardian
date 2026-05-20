"""
Main orchestration harness for the PR Governance Agent.

Design note: The reference codebase has no routing primitive (single Agent,
no state machine). This orchestrator therefore implements a Python-function
router that calls subagents in order. The routing table is:
  parse → governance_sweep → pattern_recognition → aggregate → done

Both CLI and HTTP share this exact function.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Optional

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"


def run_review(
    pr_fixture: dict,
    progress_cb: Optional[Callable[[str, str], None]] = None,
) -> dict:
    """
    Run the full PR governance review pipeline.

    Args:
        pr_fixture: PR fixture dict matching the Step 2d schema
        progress_cb: optional callback(phase, message) for streaming progress to callers

    Returns:
        Review dict matching the Step 5 output contract, also written to
        output/reviews/<pr_id>.json
    """
    from agent.context import Context
    from agent.pr_parser import parse_pr
    from agent.subagents.governance import run_governance_subagent
    from agent.subagents.pattern import run_pattern_subagent

    def emit(phase: str, message: str) -> None:
        if progress_cb:
            progress_cb(phase, message)

    # ── Route: parse ───────────────────────────────────────────────────────
    pr_id = pr_fixture.get("pr_id", "PR-UNKNOWN")
    emit("parse", f"Parsing PR {pr_id}…")

    ctx = Context(pr_id=pr_id, status="running")
    ctx.pr_data = parse_pr(pr_fixture)
    ctx.save()

    services = ctx.pr_data.get("services_touched", [])
    files = [f["path"] for f in ctx.pr_data.get("files_changed", [])]
    emit("parse", f"Parsed {len(files)} file(s); services: {services or ['(none inferred)']}")

    # ── Route: governance sweep ────────────────────────────────────────────
    emit("governance", "Running governance sweep (secrets · PII · credentials)…")
    try:
        ctx.governance_findings = run_governance_subagent(ctx)
        ctx.save()
        n = len(ctx.governance_findings)
        emit("governance", f"Done — {n} finding(s)")
    except Exception as exc:
        ctx.governance_findings = []
        ctx.save()
        emit("governance", f"Error: {exc}")

    # ── Route: pattern recognition ─────────────────────────────────────────
    emit("pattern", "Running pattern recognition (CMDB · incidents · lessons learned)…")
    try:
        ctx.pattern_findings = run_pattern_subagent(ctx)
        ctx.save()
        n = len(ctx.pattern_findings)
        emit("pattern", f"Done — {n} finding(s)")
    except Exception as exc:
        ctx.pattern_findings = []
        ctx.save()
        emit("pattern", f"Error: {exc}")

    # ── Route: aggregate ───────────────────────────────────────────────────
    emit("report", "Aggregating findings and writing report…")
    review = _aggregate(ctx)
    ctx.status = "complete"
    ctx.save()

    output_path = OUTPUT_DIR / "reviews" / f"{pr_id}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(review, indent=2))
    emit("report", f"Review complete — status={review['status']}, path={output_path}")

    return review


# ── Aggregation ────────────────────────────────────────────────────────────


def _aggregate(ctx) -> dict:
    """Build the Step 5 output contract from the context."""
    gov = ctx.governance_findings
    pat = ctx.pattern_findings

    # Violation counts by category
    category_counts: dict[str, int] = {}
    for f in gov:
        cat = _category(f.get("rule_id", ""))
        category_counts[cat] = category_counts.get(cat, 0) + 1
    for _ in pat:
        category_counts["pattern"] = category_counts.get("pattern", 0) + 1

    # Comments (one per finding)
    comments = []
    for f in gov:
        comments.append({
            "file": f.get("file", "unknown"),
            "line": f.get("line"),
            "body": f.get("rationale", f.get("snippet", "")),
            "severity": f.get("severity", "med"),
        })
    for f in pat:
        comments.append({
            "file": f.get("file", "unknown"),
            "line": f.get("line"),
            "body": f.get("rationale", ""),
            "severity": f.get("severity", "med"),
        })

    # Recommendations from pattern findings with linked evidence
    recommendations = []
    for f in pat:
        if f.get("linked_evidence"):
            recommendations.append({
                "title": _rec_title(f),
                "body": f.get("rationale", ""),
                "linked_evidence": f.get("linked_evidence", []),
            })

    return {
        "pr_id": ctx.pr_id,
        "status": "issues_found" if (gov or pat) else "clean",
        "summary": {
            "violations": [
                {"category": cat, "count": count}
                for cat, count in sorted(category_counts.items())
            ]
        },
        "comments": comments,
        "recommendations": recommendations,
        "raw_findings": {"governance": gov, "patterns": pat},
        "context_snapshot": {
            "pr_data": ctx.pr_data,
            "tool_call_log": ctx.tool_call_log,
        },
    }


def _category(rule_id: str) -> str:
    secrets = {"aws_access_key", "aws_secret_key", "private_key_header",
               "connection_string", "hardcoded_password", "generic_api_key", "bearer_token"}
    pii = {"pii_in_log", "email_address"}
    if rule_id in secrets:
        return "secrets"
    if rule_id in pii:
        return "pii"
    return "other"


def _rec_title(finding: dict) -> str:
    evidence = finding.get("linked_evidence", [])
    rule = finding.get("rule_id", "pattern")
    if evidence:
        return f"Historical risk: {evidence[0]}"
    return f"Risk pattern: {rule}"
