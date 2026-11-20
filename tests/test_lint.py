from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from helpers import ROOT, load

lint = load("scripts/lint_skills.py", "lint_skills")

GOOD_DESCRIPTION = (
    "Summarise customer support tickets into a weekly digest with themes, counts and example quotes. "
    "Use this whenever the user shares a ticket export or asks what customers complained about this week."
)


def make_skill(root: Path, name: str, frontmatter: str, body: str = "# Title\n\nDo the thing.\n", files: dict | None = None) -> Path:
    d = root / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(f"---\n{frontmatter}\n---\n\n{body}", encoding="utf-8")
    for rel, content in (files or {}).items():
        (d / rel).parent.mkdir(parents=True, exist_ok=True)
        (d / rel).write_text(content, encoding="utf-8")
    return d


class LintTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def fm(self, name="ticket-digest", description=GOOD_DESCRIPTION, extra=""):
        return f"name: {name}\ndescription: {description}\nlicense: MIT{extra}"

    def test_valid_skill_passes(self):
        d = make_skill(self.root, "ticket-digest", self.fm(), "# Digest\n\nSee `references/themes.md`.\n", {"references/themes.md": "x"})
        r = lint.lint_skill(d)
        self.assertEqual(r.errors, [])
        self.assertEqual(r.warnings, [])

    def test_missing_skill_md(self):
        d = self.root / "empty"
        d.mkdir()
        self.assertIn("SKILL.md not found.", lint.lint_skill(d).errors)

    def test_missing_frontmatter(self):
        d = self.root / "nofm"
        d.mkdir()
        (d / "SKILL.md").write_text("# Hi\n")
        self.assertTrue(any("frontmatter" in e for e in lint.lint_skill(d).errors))

    def test_name_rules(self):
        cases = {
            "Bad_Name": "kebab-case",
            "claude-helper": "reserved word",
            "other-name": "does not match folder",
        }
        for i, (name, expected) in enumerate(cases.items()):
            folder = name if expected != "does not match folder" else f"folder-{i}"
            d = make_skill(self.root, folder, self.fm(name=name))
            errors = " ".join(lint.lint_skill(d).errors)
            self.assertIn(expected, errors, name)

    def test_description_rules(self):
        d = make_skill(self.root, "a1", self.fm(name="a1", description="x" * 1100))
        self.assertTrue(any("max 1024" in e for e in lint.lint_skill(d).errors))
        d = make_skill(self.root, "a2", self.fm(name="a2", description="Formats <xml> things. Use this whenever needed and more words to be long enough for the check to pass here " * 2))
        self.assertTrue(any("angle brackets" in e for e in lint.lint_skill(d).errors))
        d = make_skill(self.root, "a3", self.fm(name="a3", description="Formats things."))
        warnings = " ".join(lint.lint_skill(d).warnings)
        self.assertIn("only 15 characters", warnings)
        self.assertIn("no trigger guidance", warnings)

    def test_unknown_key(self):
        d = make_skill(self.root, "ticket-digest", self.fm(extra="\nversion: 2"))
        self.assertTrue(any("Unknown frontmatter key" in e for e in lint.lint_skill(d).errors))

    def test_referenced_files_must_exist(self):
        d = make_skill(self.root, "ticket-digest", self.fm(), "# T\n\nRun `scripts/missing.py` and read [guide](references/guide.md).\n")
        errors = lint.lint_skill(d).errors
        self.assertIn("Referenced file does not exist: scripts/missing.py", errors)
        self.assertIn("Referenced file does not exist: references/guide.md", errors)

    def test_unreferenced_and_broken_scripts(self):
        d = make_skill(self.root, "ticket-digest", self.fm(), "# T\n\nRun `scripts/run.py`.\n",
                       {"scripts/run.py": "#!/usr/bin/env python3\ndef broken(:\n", "assets/orphan.md": "x"})
        r = lint.lint_skill(d)
        self.assertTrue(any("does not compile" in e for e in r.errors))
        self.assertIn("Bundled file is never referenced from SKILL.md: assets/orphan.md", r.warnings)

    def test_nested_skill_md_rejected(self):
        d = make_skill(self.root, "ticket-digest", self.fm(), files={"references/SKILL.md": "x"})
        self.assertTrue(any("Extra SKILL.md" in e for e in lint.lint_skill(d).errors))

    def test_repository_skills_pass_strict(self):
        failures = {}
        for d in sorted((ROOT / "skills").iterdir()):
            r = lint.lint_skill(d)
            if r.errors or r.warnings:
                failures[d.name] = r.errors + r.warnings
        self.assertEqual(failures, {})


if __name__ == "__main__":
    unittest.main()
