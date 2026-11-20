# Pricing guidance

How to turn scope into a price that is defensible, consistent and easy to compare. Rates, contingency and payment terms come from `style-guide.md`.

## 1. Estimate effort per deliverable

For each deliverable, estimate **likely** effort in person-days and note the **best case**. Typical anchors for small-team web and AI projects (adjust to your history):

| Work item | Likely effort |
|---|---|
| Discovery workshop + written spec (per 1-2 stakeholders) | 2-3 days |
| Conversation design / content structure for a chatbot (per 10 intents) | 1.5-2 days |
| Integration with a well-documented API (calendar, CRM, payments) | 2-4 days |
| Integration with an undocumented or legacy system | 5-10 days, or price as discovery first |
| Each additional language (prompting, testing, copy) | 1-2 days |
| Admin dashboard (simple list + filters + export) | 3-5 days |
| QA, test scripts and UAT support | 15-20% of build effort |
| Deployment, monitoring, handover docs and training | 1.5-3 days |
| Project management | 10-15% of total effort |

If a single deliverable is over 10 days, split it - large estimates hide risk.

## 2. Convert to price

`price = likely_days × day_rate` for each line. Keep line prices exact so the client can check the maths. Add contingency as **its own line** ("Contingency, 15% of build work") calculated on build lines only - not on fixed-fee discovery or project management - and round that line to the nearest $50 (or local equivalent). Show effort in the table so the client can see what drives the price.

Third-party costs (API usage, hosting, SMS, licences) are **not** in the fee. List them separately as estimated monthly running costs with the assumption behind each estimate (for example "about 3,000 conversations per month").

## 3. Offer options when it helps

Use three options when the budget is unknown, the client asked for "a range", or there is an obvious lite version:

| Option | Purpose |
|---|---|
| Essential | Smallest version that still solves the core problem. |
| Recommended | What you would build if it were your money. Mark it. |
| Complete | Recommended plus the most valuable nice-to-haves. |

Keep the options cumulative (each includes the previous one) so they are easy to compare.

## 4. Sanity checks

- Does the total fit the client's budget signal? If not, say so and point to the option that does, rather than shaving estimates silently.
- Is the price per week of calendar time plausible for the team size?
- Recompute every total by hand from the rows.
