# Roaster's Choice launch - voice check

Drafts: [`linkedin.md`](linkedin.md), [`instagram.md`](instagram.md), [`email.md`](email.md). Checked against `input/voice-guide.md` with `scripts/check_draft.py` and `references/self-check-rubric.md`.

## How the drafts changed during checking

First checker run (before revision):

```text
linkedin.md [linkedin]: FAIL (length 142/250 words, longest sentence 28/22, reading ease 77, ...)
  FAIL  Sentence has 28 words (max 22): "Each delivery is the single origin Tuan and I are most excited about t..."
instagram.md [instagram]: FAIL (length 80/200 words, longest sentence 27/22, reading ease 80, ...)
  FAIL  Sentence has 27 words (max 22): "Every 2 or 4 weeks you get the single origin we're most excited about,..."
email.md [email]: PASS (length 172/350 words, longest sentence 19/22, reading ease 81, ...)
```

- Split the two long sentences (both were trying to explain the subscription and the card at once).
- Rubric gate G2 caught one invented claim in the email - "lighter and brighter than our house coffees" is not in the brief - so it was removed.

Final checker run ([`checker-final.txt`](checker-final.txt)):

```text
linkedin.md [linkedin]: PASS (length 144/250 words, longest sentence 17/22, reading ease 78, emoji 0/1, exclamations 0/1, hashtags 3/3)
instagram.md [instagram]: PASS (length 80/200 words, longest sentence 14/22, reading ease 80, emoji 1/1, exclamations 0/1, hashtags 3/3)
email.md [email]: PASS (length 163/350 words, longest sentence 19/22, reading ease 81, emoji 0/1, exclamations 0/1, hashtags 0/3)
```

## Rubric scores

```text
Voice check - LinkedIn
Checker: PASS · Gates: G1 ✓ G2 ✓ G3 ✓ G4 ✓ G5 ✓
Scores: trait 5 · benefit 4 · specific 5 · clarity 5 · vocabulary 5 · CTA 4
Notes: Founder point of view as the guide asks. "Benefit" is 4 because the hook is about the roasters, not the reader - alternative hook below.

Voice check - Instagram
Checker: PASS · Gates: G1 ✓ G2 ✓ G3 ✓ G4 ✓ G5 ✓
Scores: trait 5 · benefit 5 · specific 5 · clarity 5 · vocabulary 5 · CTA 4
Notes: Uses the single emoji allowed. "Link in bio" is the only CTA Instagram captions support.

Voice check - Email
Checker: PASS · Gates: G1 ✓ G2 ✓ G3 ✓ G4 ✓ G5 ✓
Scores: trait 5 · benefit 5 · specific 5 · clarity 5 · vocabulary 5 · CTA 5
Notes: No emoji (the guide bans them in email), one link, signed "Mai & Tuan". Separate line for existing subscribers so they don't sign up twice.
```

## Alternative opening lines (LinkedIn)

1. *(used)* "Most weeks, one coffee on our table gets all the attention. From 7 December, that's the one we'll send you."
2. "You don't have to choose your next coffee anymore. From 7 December, we choose it for you."

Option 2 leads with the reader's benefit and would raise the "benefit" score to 5; option 1 is more personal for a founder post.

## To confirm before publishing

- No placeholders were needed: every fact came from the brief.
- "150 spots this month" appears in all three pieces - if spots run out before the email is sent, change it to the number left.
- Instagram uses `#roasterschoice`; check that the tag is not already used by another brand.
