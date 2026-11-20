# Self-check rubric

Score each draft before handing it over. A draft ships only if every **gate** passes and every **scored criterion** is 4 or higher.

## Gates (pass / fail)

| Gate | Fails when |
|---|---|
| G1 Checker | `scripts/check_draft.py` exits non-zero (banned word, limits exceeded). |
| G2 Facts | Any number, price, date, name or claim is not in the brief or the voice guide's allowed claims. |
| G3 One CTA | There is no call to action, or more than one competing one. |
| G4 Channel fit | Wrong structure for the channel (e.g. no subject line for an email). |
| G5 Placeholders | A required fact is missing and was invented instead of marked as `[PLACEHOLDER]`. |

## Scored criteria (1-5)

| Criterion | 1 | 3 | 5 |
|---|---|---|---|
| **Trait fit** | Generic marketing voice; could be any brand. | Some traits present, slips into a "we are not" tone in places. | Every line sounds like the guide's on-voice examples. |
| **Reader benefit first** | Opens with the brand's excitement ("We're thrilled..."). | Benefit appears, but after preamble. | First line tells the reader what's in it for them. |
| **Specificity** | Vague adjectives, no concrete detail. | Some concrete details. | Concrete nouns, numbers and sensory detail from the brief. |
| **Clarity** | Needs re-reading; jargon. | Clear but wordy. | Effortless to read aloud; every sentence earns its place. |
| **Vocabulary** | Uses "we don't say" words or clichés. | Neutral vocabulary. | Uses the brand's own words naturally. |
| **CTA strength** | CTA unclear or buried. | CTA present but generic ("Learn more"). | CTA is specific, low-friction and matches the goal. |

## Reporting format

```text
Voice check - <channel>
Checker: PASS (words 148/200, longest sentence 21/24, reading ease 68, emoji 0/2, ! 1/1)
Gates: G1 ✓ G2 ✓ G3 ✓ G4 ✓ G5 ✓
Scores: trait 5 · benefit 4 · specific 5 · clarity 4 · vocabulary 5 · CTA 4
Notes: <one line on the main trade-off or what to confirm>
```
