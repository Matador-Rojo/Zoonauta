"""Prueba el hook .claude/hooks/proteger_git.py: órdenes que deben bloquearse (2) y permitirse (0)."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / ".claude" / "hooks" / "proteger_git.py"
BLOQUEAR = ["git add -A", "git add .", "git add --all", "git commit -am x", "git push origin x",
            "git reset --hard HEAD", "git clean -fd", "git stash", "git checkout -- a.txt", "git restore a"]
PERMITIR = ["git add docs/a.md", 'git commit -m "x"', "git status", "git diff main -- a", "git log -3", "git show main:a"]


def _codigo(orden: str) -> int:
    entrada = json.dumps({"tool_input": {"command": orden}})
    return subprocess.run([sys.executable, str(HOOK)], input=entrada, text=True, capture_output=True).returncode


class HookGit(unittest.TestCase):
    def test_bloquea(self):
        for orden in BLOQUEAR:
            self.assertEqual(_codigo(orden), 2, orden)

    def test_permite(self):
        for orden in PERMITIR:
            self.assertEqual(_codigo(orden), 0, orden)


if __name__ == "__main__":
    unittest.main()
