#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LOG_PATH = Path(os.environ.get("BLOCK_DESTRUCTIVE_BASH_LOG_PATH", Path.home() / ".claude" / "hooks" / "blocked.log"))


PATTERNS = [
    (
        "rm -rf",
        re.compile(r"(^|[\s;&|()])rm\s+-(?=[A-Za-z]*r)(?=[A-Za-z]*f)[A-Za-z]+\b", re.IGNORECASE),
        "recursive force removal can delete large parts of the filesystem",
    ),
    (
        "DROP TABLE",
        re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
        "DROP TABLE permanently removes database tables",
    ),
    (
        "TRUNCATE",
        re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
        "TRUNCATE can erase all rows from a table",
    ),
    (
        "git push --force",
        re.compile(r"\bgit\s+push\b(?:(?![;&|]).)*(?:--force(?:-with-lease)?|-f\b)", re.IGNORECASE | re.DOTALL),
        "force-pushing can overwrite shared Git history",
    ),
]


def _delete_without_where(command: str) -> bool:
    for statement in re.split(r"[;\n]", command):
        if re.search(r"\bDELETE\s+FROM\b", statement, re.IGNORECASE) and not re.search(
            r"\bWHERE\b", statement, re.IGNORECASE
        ):
            return True
    return False


def classify(command: str) -> tuple[bool, str, str]:
    for name, pattern, reason in PATTERNS:
        if pattern.search(command):
            return True, name, reason

    if _delete_without_where(command):
        return True, "DELETE FROM without WHERE", "DELETE FROM without a WHERE clause can erase an entire table"

    return False, "", ""


def _extract_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return ""
    command = tool_input.get("command", "")
    return command if isinstance(command, str) else ""


def _project_path(payload: dict[str, Any]) -> str:
    cwd = payload.get("cwd")
    if isinstance(cwd, str) and cwd:
        return cwd
    return os.getcwd()


def log_blocked(command: str, project_path: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps({"timestamp": timestamp, "command": command, "project_path": project_path, "reason": reason}) + "\n")


def deny(reason: str, command: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Blocked destructive Bash command ({reason}): {command}",
                }
            }
        )
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    command = _extract_command(payload)
    if not command:
        return 0

    blocked, name, reason = classify(command)
    if not blocked:
        return 0

    log_blocked(command, _project_path(payload), name)
    deny(reason, command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
