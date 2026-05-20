"""ServiceNow-like incident management query tool."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

INCIDENTS_FILE = (
    Path(__file__).parent.parent / "fixtures" / "servicenow" / "incidents.json"
)
_data: dict | None = None


def _load() -> dict:
    global _data
    if _data is None:
        _data = json.loads(INCIDENTS_FILE.read_text())
    return _data


def query_incident_management(
    service_or_component: str,
    tags: Optional[list] = None,
    since: Optional[str] = None,
) -> str:
    """
    Return up to 5 most recent incidents for the given service.

    Args:
        service_or_component: service name to match in affected_services
        tags: optional list of tags — incident must match at least one
        since: optional ISO datetime string; only incidents opened after this date
    """
    incidents = _load()["incidents"]
    matches = []

    for inc in incidents:
        if service_or_component not in inc["affected_services"]:
            continue
        if since:
            try:
                inc_dt = datetime.fromisoformat(inc["opened"].replace("Z", "+00:00"))
                since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
                if inc_dt < since_dt:
                    continue
            except ValueError:
                pass
        if tags:
            # tags may be passed as a JSON string from the LLM
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except Exception:
                    tags = [tags]
            if not any(t in inc["tags"] for t in tags):
                continue
        matches.append(inc)

    matches.sort(key=lambda x: x["opened"], reverse=True)
    matches = matches[:5]

    return json.dumps({"matches": matches, "count": len(matches)}, indent=2)
