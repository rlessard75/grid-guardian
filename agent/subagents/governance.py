"""
Governance Sweep subagent.

Design: The regex scan runs deterministically (no LLM required). Results are
passed to the LLM for a context-sensitive second pass — confirming real
violations, filtering false positives, writing rationales. This avoids
relying on the LLM choosing to call a tool.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from agent.harness import Agent  # noqa: E402
from agent.context import Context  # noqa: E402

PROMPT_FILE = BASE_DIR / "prompts" / "governance_sweep.md"
LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-4-6")


def run_governance_subagent(ctx: Context) -> list[dict]:
    """
    Run the governance sweep on the PR diff stored in ctx.

    Step 1 (deterministic): regex scan via scan_diff_for_secrets.
    Step 2 (LLM): confirm findings, filter false positives, write rationales.
    """
    from tools.scan_diff import scan_diff_for_secrets

    pr = ctx.pr_data
    full_diff = pr.get("full_diff", "")

    # ── Step 1: Deterministic regex scan ──────────────────────────────────
    raw = scan_diff_for_secrets(full_diff)
    candidates = json.loads(raw)
    ctx.log_tool(
        "scan_diff_for_secrets",
        {"diff_length": len(full_diff)},
        f"{len(candidates)} regex candidate(s) found",
    )

    # ── Step 2: LLM confirmation pass ─────────────────────────────────────
    system = PROMPT_FILE.read_text()
    agent = Agent(system=system, tools=[], model=LLM_MODEL)

    dc_context = _data_classification_summary(pr.get("services_touched", []))

    if candidates:
        candidates_block = json.dumps(candidates, indent=2)
        scan_note = (
            f"The automated regex scanner found {len(candidates)} candidate finding(s):\n"
            f"```json\n{candidates_block}\n```\n\n"
            "For each candidate: confirm whether it is a real violation "
            "(not a placeholder, not example data in a test or doc comment), "
            "adjust severity if context warrants it, add the file path, and write a clear rationale.\n"
            "Also do a quick manual scan for anything the regex may have missed."
        )
    else:
        scan_note = (
            "The automated regex scanner found 0 candidates. "
            "Do a careful manual review of the diff for any secrets, credentials, "
            "or PII that the patterns may have missed."
        )

    prompt = f"""Review this pull request for security violations.

PR: {pr["pr_id"]} — {pr["title"]}
Author: {pr.get("author", "unknown")}
Services touched: {", ".join(pr.get("services_touched", []))}
Data classification: {dc_context}

Full diff:
{full_diff}

---
{scan_note}

Output your confirmed findings as a JSON code block. If none, output: ```json\n[]\n```"""

    response = agent.chat(prompt)
    findings = _parse_json_response(response)

    # Attach file path when missing
    for f in findings:
        if not f.get("file"):
            f["file"] = _infer_file(f.get("line", 0), pr.get("files_changed", []))

    return findings


# ── Helpers ────────────────────────────────────────────────────────────────


def _data_classification_summary(services: list[str]) -> str:
    try:
        from tools.cmdb import query_cmdb
        parts = []
        for svc in services:
            record = json.loads(query_cmdb(svc))
            if record:
                parts.append(
                    f"{svc}: {record.get('data_classification', 'unknown')} "
                    f"(Tier {record.get('tier', '?')})"
                )
        return ", ".join(parts) if parts else "unknown"
    except Exception:
        return "unknown"


def _infer_file(line_num: int, files_changed: list[dict]) -> str:
    offset = 0
    for f in files_changed:
        diff_lines = f.get("diff", "").count("\n") + 1
        if offset < line_num <= offset + diff_lines:
            return f.get("path", "unknown")
        offset += diff_lines
    return files_changed[0]["path"] if files_changed else "unknown"


def _parse_json_response(response: str) -> list[dict]:
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", response)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    try:
        return json.loads(response.strip())
    except json.JSONDecodeError:
        pass
    m = re.search(r"\[[\s\S]*\]", response)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return []
