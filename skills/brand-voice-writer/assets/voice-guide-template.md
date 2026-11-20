# {{Brand}} voice guide

## Who we are, in one line

{{What we do, for whom, and why it matters - one sentence.}}

## Audience

{{Who reads our copy, what they care about, what they are tired of hearing.}}

## Personality

| We are | We are not | Sounds like |
|---|---|---|
| {{trait}} | {{exaggerated or opposite version}} | "{{short example line}}" |
| {{trait}} | {{...}} | "{{...}}" |
| {{trait}} | {{...}} | "{{...}}" |

## How we write

- Person: {{we / you / I}}
- Sentences: {{typical length; contractions yes/no}}
- Capitalisation: {{sentence case headlines? product names?}}
- Numbers and money: {{format}}
- Emoji: {{none / sparingly (max N) / freely}} · Exclamation marks: {{max per piece}}
- Hashtags: {{max per post, style}}
- Humour: {{when and how}}

## Vocabulary

| We say | We don't say |
|---|---|
| {{word}} | {{word}} |

## Claims we can and cannot make

- {{e.g. "Roasted every Monday" - yes, verifiable. "Best coffee in the city" - no.}}

## Channel notes

- {{Channel}}: {{specifics, e.g. LinkedIn: first-person from the founder, 120-200 words}}

## Examples

**On voice:** {{example}} - *why it works:* {{...}}

**Off voice:** {{example}} - *what's wrong:* {{...}}

## Machine-readable rules

Used by `scripts/check_draft.py`. Keep the keys; edit the values.

```voice-rules
avoid: {{comma-separated words and phrases}}
max_sentence_words: {{e.g. 24}}
max_exclamations: {{e.g. 1}}
max_emoji: {{e.g. 2}}
max_hashtags: {{e.g. 3}}
min_reading_ease: {{e.g. 55}}
```
