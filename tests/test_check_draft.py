import unittest

from helpers import ROOT, load

check = load("skills/brand-voice-writer/scripts/check_draft.py", "check_draft")
GUIDE = (ROOT / "examples/brand-voice-writer/input/voice-guide.md").read_text()
RULES = check.parse_rules(GUIDE)


class CheckDraftTests(unittest.TestCase):
    def test_rules_parsed_from_guide(self):
        self.assertIn("artisanal", RULES["avoid"])
        self.assertIn("best coffee", RULES["avoid"])
        self.assertEqual(RULES["max_sentence_words"], 22)
        self.assertEqual(RULES["max_emoji"], 1)

    def test_template_placeholders_rejected(self):
        template = (ROOT / "skills/brand-voice-writer/assets/voice-guide-template.md").read_text()
        with self.assertRaises(ValueError):
            check.parse_rules(template)

    def test_banned_words_and_counts(self):
        draft = "Our artisanal beans are AMAZING!! Try the best   coffee today 😀😀 #a #b #c #d"
        result = check.check(draft, RULES, "instagram")
        self.assertFalse(result["passed"])
        terms = {h["term"] for h in result["metrics"]["banned_terms"]}
        self.assertEqual(terms, {"artisanal", "amazing", "best coffee"})
        joined = " ".join(result["failures"])
        self.assertIn("2 exclamations", joined)
        self.assertIn("2 emoji", joined)
        self.assertIn("4 hashtags", joined)

    def test_no_false_positive_inside_words(self):
        result = check.check("We crafted a plan. Handcrafted mugs are nice.", {"avoid": ["craft"]}, "generic")
        self.assertTrue(result["passed"])

    def test_sentence_length_and_channel_limit(self):
        long_sentence = " ".join(["word"] * 30) + "."
        result = check.check(long_sentence, RULES, "generic")
        self.assertTrue(any("30 words" in f for f in result["failures"]))
        tweet = "a" * 281
        self.assertTrue(any("Too long for x" in f for f in check.check(tweet, {}, "x")["failures"]))

    def test_email_needs_subject(self):
        result = check.check("Hi there. This is short.", RULES, "email")
        self.assertIn("Email needs a 'Subject:' line at the top.", result["failures"])
        ok = check.check("Subject: Hello\nPreview: Short preview\n\nHi there. This is short.", RULES, "email")
        self.assertTrue(ok["passed"], ok["failures"])

    def test_recorded_example_drafts_pass(self):
        out = ROOT / "examples/brand-voice-writer/output"
        for name, channel in (("linkedin.md", "linkedin"), ("instagram.md", "instagram"), ("email.md", "email")):
            result = check.check((out / name).read_text(), RULES, channel)
            self.assertTrue(result["passed"], (name, result["failures"]))


if __name__ == "__main__":
    unittest.main()
