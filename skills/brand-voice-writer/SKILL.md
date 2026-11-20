---
name: brand-voice-writer
description: Write on-brand social posts, emails, newsletters, landing-page and product copy from a brand voice guide and a short brief, then score every draft with a self-check rubric and a deterministic checker (banned words, sentence length, exclamation marks, emoji, readability, channel length). Also builds a voice guide from scratch out of a few example texts. Use this whenever the user wants marketing or customer-facing copy that must sound like their brand - LinkedIn, X, Instagram or Facebook posts, launch announcements, email campaigns, newsletters, product descriptions, ad copy - or asks to "make this sound like us", rewrite text in their tone, or create a brand voice or tone-of-voice guide.
license: MIT
compatibility: Python 3.9+ (standard library only) for the draft checker.
metadata:
  version: "1.0.0"
  author: Cuong Nguyen
---

# Brand voice writer

Write copy that a brand's own team would mistake for their best writer's work - and prove it with a check, not a feeling.

## Inputs

1. **Voice guide** - the user's file, or one built with `assets/voice-guide-template.md`. Its machine-readable `voice-rules` block drives the checker.
2. **Brief** - what to announce or say, audience, channel(s), goal/CTA, facts and claims that may be used, deadline or offer details.
3. **Examples** (optional but valuable) - 2-5 pieces the brand considers on-voice.

If there is no voice guide, build one first: ask for (or read) 3-5 example texts, fill `assets/voice-guide-template.md` from what they actually do (sentence length, person, vocabulary, emoji, humour), show it to the user, then write. Do not invent a personality the examples don't support.

## Workflow

### 1. Internalise the voice

Read the whole guide and the examples. Write down, for yourself, the 3 traits and their "not" counterparts (e.g. *warm, not cute*), the banned words, and the channel rules for the requested channels. The "not" side is where most drafts go wrong.

### 2. Lock the facts

List the facts, numbers, prices, dates and claims from the brief. Copy may only use these. If the copy needs a fact the brief does not give (a price, a date, a statistic), write a visible placeholder like `[PRICE]` and mention it in the hand-over rather than inventing it. Marketing copy that states a wrong price or an unprovable claim causes real damage.

### 3. Draft per channel

Follow `references/channel-formats.md` for structure and length per channel. Lead with the reader's benefit, not the brand's excitement. One message and one call to action per piece. Write 2 variants of the opening line for short social posts so the user can choose.

### 4. Check every draft

Run the deterministic checker on each draft (save drafts as files first):

```bash
python scripts/check_draft.py --guide voice-guide.md --channel linkedin draft-linkedin.md
```

It reports banned words, over-long sentences, exclamation marks, emoji, hashtags, length against the channel limit and a reading-ease score, and exits non-zero when a hard rule fails. Fix and re-run until it passes.

Then score the draft with `references/self-check-rubric.md` (judgement criteria the script cannot measure: trait fit, clarity, specificity, CTA, factual grounding). Revise anything below 4 and any failed gate. If Python is unavailable, apply the rubric's gates by hand and say so.

### 5. Hand over

For each piece: the final copy (ready to paste), then a compact "Voice check" block with the checker result and rubric scores, then placeholders or assumptions the user must resolve. Keep commentary short - the user wants copy, not an essay about copy.
