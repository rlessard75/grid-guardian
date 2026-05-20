"""Parse a PR fixture dict into normalized fields for the agent pipeline."""
from __future__ import annotations

from typing import Any


def parse_pr(pr_fixture: dict[str, Any]) -> dict[str, Any]:
    """Normalize a PR fixture JSON into the canonical shape used throughout the pipeline."""
    files: list[dict] = pr_fixture.get("files_changed", [])
    return {
        "pr_id": pr_fixture["pr_id"],
        "title": pr_fixture.get("title", ""),
        "description": pr_fixture.get("description", ""),
        "author": pr_fixture.get("author", "unknown"),
        "branch": pr_fixture.get("branch", ""),
        "base_branch": pr_fixture.get("base_branch", "main"),
        "created_at": pr_fixture.get("created_at", ""),
        "files_changed": files,
        "services_touched": _extract_services(files),
        "full_diff": _join_diffs(files),
    }


def _extract_services(files: list[dict]) -> list[str]:
    """Infer service names from top-level path components (e.g. 'auth-service/config/...' → 'auth-service')."""
    services: set[str] = set()
    for f in files:
        path = f.get("path", "")
        if "/" in path:
            services.add(path.split("/")[0])
    return sorted(services)


def _join_diffs(files: list[dict]) -> str:
    return "\n\n".join(
        f"=== {f['path']} ({f.get('change_type', 'modified')}) ===\n{f.get('diff', '')}"
        for f in files
    )
