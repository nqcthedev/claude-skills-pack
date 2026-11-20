import contextlib
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT, load

gather = load("skills/code-review-checklist/scripts/gather_diff.py", "gather_diff")
GIT = ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "-c", "commit.gpgsign=false"]


@unittest.skipUnless(shutil.which("git"), "git not installed")
class GatherDiffTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.git("init", "-q", "-b", "main")
        (self.repo / "app.py").write_text("def add(a, b):\n    return a + b\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "base")

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        subprocess.run([*GIT, *args], cwd=self.repo, check=True, capture_output=True)

    def run_tool(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = gather.main(["--repo", str(self.repo), *args])
        summary = json.loads((self.repo / ".review" / "summary.json").read_text()) if code == 0 else None
        return code, summary, out.getvalue()

    def test_branch_mode_flags_risks(self):
        self.git("checkout", "-qb", "feature")
        (self.repo / "app.py").write_text(
            "import random\n\nAPI_TOKEN = 'abcd1234efgh5678'\n\n"
            "def add(a, b):\n    print(a)\n    return a + b\n\n"
            "def find(db, name):\n    return db.execute(f\"SELECT * FROM users WHERE name = '{name}'\")\n"
        )
        (self.repo / "requirements.txt").write_text("requests\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "feature work")
        code, summary, stdout = self.run_tool("--base", "main")
        self.assertEqual(code, 0)
        self.assertEqual(summary["totals"]["files"], 2)
        self.assertEqual(summary["commits"][0]["subject"], "feature work")
        types = {(f["type"], f["path"], f["line"]) for f in summary["risk_flags"]}
        self.assertIn(("possible_secret", "app.py", 3), types)
        self.assertIn(("debug_statement", "app.py", 6), types)
        self.assertIn(("possible_sql_injection", "app.py", 10), types)
        self.assertIn(("dependency_change", "requirements.txt", None), types)
        self.assertTrue(any(t == "source_without_tests" for t, _, _ in types))
        self.assertTrue(summary["checklist_path"].endswith("references/default-checklist.md"))
        self.assertIn("Risk flags", stdout)
        self.assertTrue((self.repo / ".review" / "diff.patch").read_text().startswith("diff --git"))

    def test_tests_and_repo_checklist_are_detected(self):
        self.git("checkout", "-qb", "feature")
        (self.repo / "app.py").write_text("def add(a, b):\n    return b + a\n")
        (self.repo / "tests").mkdir()
        (self.repo / "tests" / "test_app.py").write_text("def test_add():\n    assert True\n")
        (self.repo / ".code-review-checklist.md").write_text("# Team checklist\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "with tests")
        _, summary, _ = self.run_tool("--base", "main")
        self.assertEqual(summary["totals"]["test_files"], 1)
        self.assertFalse(any(f["type"] == "source_without_tests" for f in summary["risk_flags"]))
        self.assertEqual(Path(summary["checklist_path"]).name, ".code-review-checklist.md")

    def test_staged_and_working_modes(self):
        (self.repo / "app.py").write_text("def add(a, b):\n    console = 1\n    return a + b\n")
        self.git("add", "app.py")
        _, staged, _ = self.run_tool("--staged")
        self.assertEqual(staged["mode"], "staged")
        self.assertEqual(staged["totals"]["additions"], 1)
        (self.repo / "app.py").write_text("def add(a, b):\n    console = 1\n    return a - b\n")
        _, working, _ = self.run_tool("--working")
        self.assertEqual(working["totals"]["additions"], 2)

    def test_not_a_repository(self):
        with tempfile.TemporaryDirectory() as empty:
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                self.assertEqual(gather.main(["--repo", empty]), 2)

    def test_added_lines_parser_tracks_new_line_numbers(self):
        patch = "+++ b/x.py\n@@ -1,2 +10,3 @@\n context\n+added one\n-removed\n+added two\n"
        self.assertEqual(list(gather.added_lines(patch)), [("x.py", 11, "added one"), ("x.py", 12, "added two")])


if __name__ == "__main__":
    unittest.main()
