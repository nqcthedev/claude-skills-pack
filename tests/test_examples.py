"""Consistency checks on the showcase outputs in examples/."""
import re
import unittest

from helpers import ROOT

PROPOSAL = (ROOT / "examples/client-proposal/output/proposal-brightsmile-dental.md").read_text()


def money(text: str) -> int:
    return int(re.sub(r"[^\d]", "", text))


class ProposalTests(unittest.TestCase):
    def option_rows(self, name):
        start = PROPOSAL.index(f"### {name} -")
        end = PROPOSAL.index("###", start + 5)
        rows = [line for line in PROPOSAL[start:end].splitlines() if line.startswith("| ") and "$" in line]
        return rows[:-1], rows[-1]

    def test_option_tables_add_up(self):
        for name in ("Essential", "Recommended", "Complete"):
            items, total = self.option_rows(name)
            price = sum(money(r.split("|")[3]) for r in items)
            days = sum(float(r.split("|")[2].split()[0]) for r in items if r.split("|")[2].strip() != "-")
            self.assertEqual(price, money(total.split("|")[3]), name)
            self.assertAlmostEqual(days, float(total.split("|")[2].strip(" *").split()[0]), msg=name)

    def test_contingency_is_15_percent_of_build_lines(self):
        items, _ = self.option_rows("Essential")
        build = [r for r in items if not re.search(r"fixed fee|Project management|Contingency", r)]
        expected = round(sum(money(r.split("|")[3]) for r in build) * 0.15 / 50) * 50
        contingency = next(r for r in items if "Contingency" in r)
        self.assertEqual(money(contingency.split("|")[3]), expected)

    def test_no_template_placeholders_left(self):
        for path in (ROOT / "examples").rglob("output/*.md"):
            self.assertNotIn("{{", path.read_text(), path)

    def test_payment_split_matches_total(self):
        parts = re.search(r"\$([\d,]+) / \$([\d,]+) / \$([\d,]+)", PROPOSAL).groups()
        self.assertEqual(sum(money(p) for p in parts), 10970)


class SeoBriefTests(unittest.TestCase):
    def test_metadata_lengths_are_correct(self):
        brief = (ROOT / "examples/seo-page-brief/output/brief-cold-brew-ratio.md").read_text()
        for label, text in re.findall(r"\*\*(?:Title|Meta description)\*\* \((\d+) chars\): (.+)", brief):
            self.assertEqual(int(label), len(text.strip()), text)


if __name__ == "__main__":
    unittest.main()
