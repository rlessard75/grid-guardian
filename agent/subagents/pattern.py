"""
Pattern Recognition subagent.

Design: CMDB records, incident history, and lessons-learned are pre-fetched
deterministically before calling the LLM. All context is passed in the prompt
so the LLM can reason without needing to call tools. Tools remain available
for follow-up queries the LLM decides to make.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from agent.harness import Agent, Tool  # noqa: E402
from agent.context import Context  # noqa: E402

PROMPT_FILE = BASE_DIR / "prompts" / "pattern_recognition.md"
LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-4-6")


def run_pattern_subagent(ctx: Context) -> list[dict]:
    """
    Run pattern recognition on the PR stored in ctx.

    Pre-fetches CMDB, incidents, and lessons-learned, then asks the LLM to
    reason about risky patterns. Tools remain available for follow-up queries.
    """
    from tools.cmdb import query_cmdb
    from tools.incidents import query_incident_management
    from tools.lessons_learned import query_lessons_learned

    pr = ctx.pr_data
    services = pr.get("services_touched", [])

    # ── Pre-fetch CMDB records ─────────────────────────────────────────────
    cmdb_records = {}
    for svc in services:
        result = query_cmdb(svc)
        record = json.loads(result)
        cmdb_records[svc] = record
        ctx.log_tool(
            "query_cmdb",
            {"service_name": svc},
            f"tier={record.get('tier')} dc={record.get('data_classification')}"
            if record else "not found",
        )

    # ── Pre-fetch incidents ────────────────────────────────────────────────
    incident_results = {}
    for svc in services:
        result = query_incident_management(svc)
        data = json.loads(result)
        incident_results[svc] = data
        ctx.log_tool(
            "query_incident_management",
            {"service_or_component": svc},
            f"{data['count']} incident(s) found",
        )

    # ── Pre-fetch lessons learned ──────────────────────────────────────────
    ll_query = f"{pr.get('title', '')} {pr.get('description', '')} {_diff_keywords(pr)}"
    ll_result = query_lessons_learned(ll_query, k=3)
    ctx.log_tool(
        "query_lessons_learned",
        {"query_text": ll_query[:80] + "..."},
        ll_result[:120] + "..." if len(ll_result) > 120 else ll_result,
    )

    # ── Build prompt with pre-fetched context ──────────────────────────────
    system = PROMPT_FILE.read_text()

    cmdb_block = json.dumps(cmdb_records, indent=2) if cmdb_records else "No CMDB records found."
    incidents_block = json.dumps(incident_results, indent=2) if incident_results else "No incidents found."

    diff_summary = _summarize_diff(pr)

    # Wire tools for any follow-up queries the LLM wants to make
    def _cmdb(service_name: str) -> str:
        r = query_cmdb(service_name)
        ctx.log_tool("query_cmdb", {"service_name": service_name}, r[:80])
        return r

    def _incidents(service_or_component: str, tags=None, since=None) -> str:
        r = query_incident_management(service_or_component, tags, since)
        ctx.log_tool("query_incident_management", {"service_or_component": service_or_component}, r[:80])
        return r

    def _lessons(query_text: str, k: int = 3) -> str:
        r = query_lessons_learned(query_text, k)
        ctx.log_tool("query_lessons_learned", {"query_text": query_text[:60]}, r[:80])
        return r

    tools = [
        Tool(
            name="query_cmdb",
            description="Return the CMDB service record for a service name.",
            parameters={"type": "object", "properties": {
                "service_name": {"type": "string"}}, "required": ["service_name"]},
            handler=_cmdb,
        ),
        Tool(
            name="query_incident_management",
            description="Return recent incidents for a service. Optional: tags (array), since (ISO date).",
            parameters={"type": "object", "properties": {
                "service_or_component": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "since": {"type": "string"}}, "required": ["service_or_component"]},
            handler=_incidents,
        ),
        Tool(
            name="query_lessons_learned",
            description="Search post-mortem lessons-learned documents.",
            parameters={"type": "object", "properties": {
                "query_text": {"type": "string"},
                "k": {"type": "integer", "default": 3}}, "required": ["query_text"]},
            handler=_lessons,
        ),
    ]

    agent = Agent(system=system, tools=tools, model=LLM_MODEL)

    prompt = f"""Analyze this pull request for risky patterns based on historical incidents and lessons learned.

PR: {pr["pr_id"]} — {pr["title"]}
Description: {pr.get("description", "")}
Author: {pr.get("author", "unknown")}
Services touched: {", ".join(services) or "(none inferred)"}
Files changed: {", ".join(f["path"] for f in pr.get("files_changed", []))}

Diff summary:
{diff_summary}

---
CMDB records (pre-fetched):
```json
{cmdb_block}
```

Incident history (pre-fetched):
```json
{incidents_block}
```

Lessons learned (pre-fetched, top matches):
{ll_result}

---
Based on the above context, identify any risky patterns. You may call the tools \
for additional queries if needed.

Output your pattern findings as a JSON code block. If none, output: ```json\n[]\n```"""

    response = agent.chat(prompt)
    return _parse_json_response(response)


# ── Helpers ────────────────────────────────────────────────────────────────


def _diff_keywords(pr: dict) -> str:
    """Extract key terms from added lines to help the lessons-learned query."""
    words = []
    for f in pr.get("files_changed", []):
        for line in f.get("diff", "").split("\n"):
            if line.startswith("+") and not line.startswith("+++"):
                words.extend(line[1:].split())
    # Return unique meaningful words, capped
    seen, result = set(), []
    for w in words:
        w = w.strip("\"',:{}[]()").lower()
        if len(w) > 3 and w not in seen:
            seen.add(w)
            result.append(w)
        if len(result) >= 20:
            break
    return " ".join(result)


def _summarize_diff(pr: dict) -> str:
    lines = []
    for f in pr.get("files_changed", []):
        diff = f.get("diff", "")
        removed = [ln[1:].strip() for ln in diff.split("\n")
                   if ln.startswith("-") and not ln.startswith("---")]
        added = [ln[1:].strip() for ln in diff.split("\n")
                 if ln.startswith("+") and not ln.startswith("+++")]
        if added or removed:
            lines.append(f"  {f['path']} ({f.get('change_type', 'modified')}):")
            for ln in removed[:5]:
                lines.append(f"    - {ln}")
            for ln in added[:5]:
                lines.append(f"    + {ln}")
    return "\n".join(lines)


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
