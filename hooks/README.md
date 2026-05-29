# Destructive Bash Command Hook

This Claude Code `PreToolUse` hook blocks destructive Bash commands before execution and logs every blocked attempt to `~/.claude/hooks/blocked.log`.

## Install

Run these two commands from the repository root:

```bash
mkdir -p ~/.claude/hooks && cp hooks/block_destructive_bash.py ~/.claude/hooks/block_destructive_bash.py && chmod +x ~/.claude/hooks/block_destructive_bash.py
python3 hooks/install_destructive_command_hook.py
```

## What It Blocks

- `rm -rf` and equivalent flag orderings such as `rm -fr`
- `DROP TABLE`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

Safe commands continue through Claude Code's normal permission flow without hook output.

## Hook Output

When blocked, the hook returns a Claude Code `PreToolUse` decision:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked destructive Bash command (...)"
  }
}
```

Each blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSON Lines with timestamp, attempted command, project path, and matched rule.
