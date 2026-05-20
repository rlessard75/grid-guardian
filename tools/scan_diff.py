"""
Deterministic regex scanner for secrets, credentials, and PII patterns in diffs.
Applied only to added lines (starting with '+', excluding '+++').
"""
from __future__ import annotations

import json
import re
from typing import Any

# (rule_id, compiled_pattern, severity)
_PATTERNS: list[tuple[str, re.Pattern, str]] = [
    # Secrets & credentials
    ("aws_access_key",
     re.compile(r"AKIA[0-9A-Z]{16}"),
     "critical"),
    ("aws_secret_key",
     re.compile(r"(?i)(?:aws[_\-]?secret[_\-]?access[_\-]?key|aws[_\-]?secret)\s*[=:]\s*['\"]?[A-Za-z0-9/+=]{30,}"),
     "critical"),
    ("private_key_header",
     re.compile(r"-----BEGIN\s+(?:RSA\s+|EC\s+|OPENSSH\s+)?PRIVATE KEY-----"),
     "critical"),
    ("connection_string",
     re.compile(r"(?i)(?:postgresql|mysql|mongodb|mssql|redis|amqp)://[^\s'\"]+:[^\s'\"@]+@[\w.\-]+"),
     "critical"),
    ("hardcoded_password",
     re.compile(r"(?i)(?:password|passwd|pwd)\s*[=:]\s*['\"][^'\"\\]{6,}['\"]"),
     "high"),
    ("generic_api_key",
     re.compile(r"(?i)(?:api[_\-]?key|apikey|auth[_\-]?token)\s*[=:]\s*['\"][A-Za-z0-9_\-]{20,}['\"]"),
     "high"),
    ("bearer_token",
     re.compile(r"(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*"),
     "high"),
    # PII leaking through log calls — matches log.X(...email...) or log.X(...user.dict()...)
    ("pii_in_log",
     re.compile(r"(?i)(?:log\.\w+|logger\.\w+|logging\.\w+)\s*\(.*?(?:email|phone|ssn|dob|cardholder|\.dict\(\)|user\.dict|request\.json|request\.body)"),
     "high"),
    # Loose PII / infrastructure
    ("email_address",
     re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"),
     "med"),
    ("internal_hostname",
     re.compile(r"\b[\w\-]+\.(?:internal|corp|local|intra)\b"),
     "med"),
]


def scan_diff_for_secrets(diff_text: str) -> str:
    """
    Scan added lines in a unified diff for credential and PII patterns.
    Returns a JSON array of candidate findings.
    Each finding: { rule_id, severity, line, snippet, match }
    """
    findings: list[dict[str, Any]] = []
    lines = diff_text.split("\n")

    for line_num, line in enumerate(lines, start=1):
        # Only scan added lines, not context lines or diff headers
        if not line.startswith("+") or line.startswith("+++"):
            continue
        content = line[1:]  # strip leading +

        for rule_id, pattern, severity in _PATTERNS:
            for m in pattern.finditer(content):
                start = max(0, m.start() - 20)
                end = min(len(content), m.end() + 20)
                snippet = content[start:end].strip()
                findings.append({
                    "rule_id": rule_id,
                    "severity": severity,
                    "line": line_num,
                    "snippet": snippet,
                    "match": m.group(),
                })

    return json.dumps(findings, indent=2)
