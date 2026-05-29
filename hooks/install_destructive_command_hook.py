#!/usr/bin/env python3
"""Install the destructive Bash command hook in ~/.claude/settings.json."""

from __future__ import annotations

import json
from pathlib import Path


CLAUDE_DIR = Path.home() / ".claude"
SETTINGS_PATH = CLAUDE_DIR / "settings.json"
HOOK_PATH = CLAUDE_DIR / "hooks" / "block_destructive_bash.py"


HOOK_ENTRY = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": str(HOOK_PATH),
        }
    ],
}


def load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return {}
    with SETTINGS_PATH.open("r", encoding="utf-8") as settings_file:
        return json.load(settings_file)


def main() -> int:
    CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
    settings = load_settings()
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    if HOOK_ENTRY not in pre_tool_use:
        pre_tool_use.append(HOOK_ENTRY)

    with SETTINGS_PATH.open("w", encoding="utf-8") as settings_file:
        json.dump(settings, settings_file, indent=2)
        settings_file.write("\n")

    print(f"Installed PreToolUse hook in {SETTINGS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
