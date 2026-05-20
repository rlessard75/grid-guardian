"""CMDB query tool — returns service records from fixtures/cmdb/cmdb.json."""
from __future__ import annotations

import json
from pathlib import Path

CMDB_FILE = Path(__file__).parent.parent / "fixtures" / "cmdb" / "cmdb.json"
_data: dict | None = None


def _load() -> dict:
    global _data
    if _data is None:
        _data = json.loads(CMDB_FILE.read_text())
    return _data


def query_cmdb(service_name: str) -> str:
    """Return the CMDB service record as JSON, or 'null' if not found."""
    for service in _load()["services"]:
        if service["name"] == service_name or service["service_id"] == service_name:
            return json.dumps(service, indent=2)
    return "null"
