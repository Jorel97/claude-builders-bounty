import json
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main


HOOK = Path(__file__).resolve().parents[1] / "hooks" / "block_destructive_bash.py"


def run_hook(command: str, log_path: Path) -> subprocess.CompletedProcess:
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": "/tmp/example-project",
        "hook_event_name": "PreToolUse",
    }
    env = os.environ.copy()
    env["BLOCK_DESTRUCTIVE_BASH_LOG_PATH"] = str(log_path)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


class BlockDestructiveBashTests(TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.log_path = Path(self.temp_dir.name) / "blocked.log"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def assert_denied(self, command: str) -> None:
        result = run_hook(command, self.log_path)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(result.stdout)
        output = json.loads(result.stdout)
        decision = output["hookSpecificOutput"]
        self.assertEqual(decision["hookEventName"], "PreToolUse")
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertTrue(self.log_path.exists())

    def assert_allowed(self, command: str) -> None:
        result = run_hook(command, self.log_path)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_blocks_rm_rf_variants(self):
        self.assert_denied("rm -rf build")
        self.assert_denied("rm -fr /tmp/demo")

    def test_blocks_sql_destructive_commands(self):
        self.assert_denied("psql -c 'DROP TABLE users'")
        self.assert_denied("psql -c 'TRUNCATE audit_log'")
        self.assert_denied("psql -c 'DELETE FROM users'")

    def test_allows_delete_with_where_clause(self):
        self.assert_allowed("psql -c 'DELETE FROM users WHERE id = 1'")

    def test_blocks_git_force_push(self):
        self.assert_denied("git push --force origin main")
        self.assert_denied("git push -f origin main")

    def test_allows_normal_commands(self):
        self.assert_allowed("npm test")
        self.assert_allowed("git push origin main")
        self.assert_allowed("rm build/output.txt")


if __name__ == "__main__":
    main()
