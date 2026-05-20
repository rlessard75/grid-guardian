"""
Shared Context object — passed between all pipeline steps and persisted to disk.
Every step reads from and writes to Context; the final state feeds the output JSON.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"


@dataclass
class Context:
    pr_id: str
    pr_data: dict = field(default_factory=dict)
    governance_findings: list[dict] = field(default_factory=list)
    pattern_findings: list[dict] = field(default_factory=list)
    tool_call_log: list[dict] = field(default_factory=list)
    status: str = "pending"

    def log_tool(self, tool: str, args: dict, result_summary: str) -> None:
        """Record a tool invocation to the audit log."""
        self.tool_call_log.append({
            "tool": tool,
            "args": args,
            "result_summary": result_summary,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def to_dict(self) -> dict[str, Any]:
        return {
            "pr_id": self.pr_id,
            "pr_data": self.pr_data,
            "governance_findings": self.governance_findings,
            "pattern_findings": self.pattern_findings,
            "tool_call_log": self.tool_call_log,
            "status": self.status,
        }

    def save(self) -> None:
        path = OUTPUT_DIR / "context" / f"{self.pr_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, pr_id: str) -> "Context":
        path = OUTPUT_DIR / "context" / f"{pr_id}.json"
        data = json.loads(path.read_text())
        ctx = cls(pr_id=data["pr_id"])
        ctx.pr_data = data["pr_data"]
        ctx.governance_findings = data["governance_findings"]
        ctx.pattern_findings = data["pattern_findings"]
        ctx.tool_call_log = data["tool_call_log"]
        ctx.status = data["status"]
        return ctx
