import contextlib
import copy
import csv
import io
import json
import unittest

from helpers import ROOT, load

tool = load("skills/meeting-to-tasks/scripts/tasks_tool.py", "tasks_tool")
EXAMPLE = json.loads((ROOT / "examples/meeting-to-tasks/output/tasks.json").read_text())
TRANSCRIPT = (ROOT / "examples/meeting-to-tasks/input/transcript.txt").read_text()


class ValidateTests(unittest.TestCase):
    def errors_for(self, mutate):
        data = copy.deepcopy(EXAMPLE)
        mutate(data)
        return tool.validate(data, TRANSCRIPT)[0]

    def test_example_is_valid_against_transcript(self):
        errors, warnings = tool.validate(EXAMPLE, TRANSCRIPT)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_owner_must_be_attendee(self):
        errors = self.errors_for(lambda d: d["action_items"][0].update(owner="Somebody Else"))
        self.assertTrue(any("not an attendee" in e for e in errors))

    def test_due_date_rules(self):
        self.assertTrue(any("before the meeting" in e for e in self.errors_for(lambda d: d["action_items"][0].update(due_date="2026-11-01"))))
        self.assertTrue(any("YYYY-MM-DD" in e for e in self.errors_for(lambda d: d["action_items"][0].update(due_date="Friday"))))
        self.assertTrue(any("requires due_date null" in e for e in self.errors_for(lambda d: d["action_items"][0].update(due_basis="none"))))
        self.assertTrue(any("due_date is null" in e for e in self.errors_for(lambda d: d["action_items"][6].update(due_basis="explicit"))))

    def test_quote_must_appear_in_transcript(self):
        errors = self.errors_for(lambda d: d["action_items"][1].update(source_quote="I will rewrite the whole backend tonight."))
        self.assertTrue(any("not found in transcript" in e for e in errors))

    def test_quote_matching_ignores_case_and_whitespace(self):
        self.assertTrue(tool._quote_in_source("i'll SEND the  email address\nafter this call.", tool._normalise(TRANSCRIPT)))
        self.assertTrue(tool._quote_in_source("Then 28, 29 ... December.", tool._normalise(TRANSCRIPT)))

    def test_dependencies(self):
        self.assertTrue(any("unknown action item" in e for e in self.errors_for(lambda d: d["action_items"][2].update(depends_on=["A99"]))))
        def cycle(d):
            d["action_items"][1]["depends_on"] = ["A3"]  # A3 already depends on A2
        self.assertTrue(any("cycle" in e for e in self.errors_for(cycle)))

    def test_duplicate_ids_and_enums(self):
        self.assertTrue(any("Duplicate id" in e for e in self.errors_for(lambda d: d["action_items"][1].update(id="A1"))))
        self.assertTrue(any("priority" in e for e in self.errors_for(lambda d: d["action_items"][0].update(priority="urgent"))))

    def test_cli_exit_codes(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(tool.main(["validate", str(ROOT / "examples/meeting-to-tasks/output/tasks.json")]), 0)


class ExportTests(unittest.TestCase):
    def rows(self, fmt):
        header, rows = tool.export_rows(EXAMPLE, fmt)
        return list(csv.reader(io.StringIO(tool.to_csv(header, rows))))

    def test_jira(self):
        table = self.rows("jira")
        self.assertEqual(table[0][:6], ["Summary", "Description", "Issue Type", "Priority", "Assignee", "Due Date"])
        self.assertEqual(table[0][6:], ["Labels", "Labels", "Labels"])
        first = table[1]
        self.assertEqual(first[3], "High")
        self.assertEqual(first[4], "hoa.tran@brightsmile.example")
        self.assertEqual(first[5], "2026-12-04")
        self.assertIn('Evidence: "I\'ll check with the provider', first[1])

    def test_asana_uses_us_dates(self):
        table = self.rows("asana")
        self.assertEqual(table[1][3], "12/04/2026")
        self.assertEqual(table[7][3], "")  # A7 has no due date

    def test_notion_and_generic(self):
        notion = self.rows("notion")
        self.assertEqual(notion[0], ["Name", "Assignee", "Due", "Priority", "Status", "Depends on", "Source"])
        self.assertEqual(notion[3][5], "A2")
        generic = self.rows("generic")
        self.assertEqual(len(generic), len(EXAMPLE["action_items"]) + 1)

    def test_recorded_example_csvs_are_current(self):
        for fmt in ("jira", "asana", "notion", "generic"):
            header, rows = tool.export_rows(EXAMPLE, fmt)
            recorded = (ROOT / f"examples/meeting-to-tasks/output/tasks-{fmt}.csv").read_text()
            self.assertEqual(recorded, tool.to_csv(header, rows), fmt)

    def test_export_refuses_invalid_data(self):
        import tempfile, os
        bad = copy.deepcopy(EXAMPLE)
        bad["action_items"][0]["owner"] = "Nobody"
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(bad, f)
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(tool.main(["export", f.name, "--format", "jira"]), 1)
        finally:
            os.unlink(f.name)


if __name__ == "__main__":
    unittest.main()
