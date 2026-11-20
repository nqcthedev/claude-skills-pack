---
name: client-proposal
description: Turn a client brief, RFP, discovery-call notes or email thread into a ready-to-send project proposal in the team's house style - executive summary, scope (in and out), deliverables, timeline with milestones, pricing table with options, assumptions, risks and next steps - plus a short cover email and a list of open questions. Use this whenever the user wants to write, draft, price, update or tighten a proposal, quote, estimate, SOW, statement of work, bid or pitch for a client or prospect, or pastes a brief and asks what to send back, even if the word "proposal" is never used.
license: MIT
metadata:
  version: "1.0.0"
  author: Cuong Nguyen
---

# Client proposal

Produce a proposal a client can say "yes" to: specific about what they get, honest about what is assumed, and priced in a way that is easy to compare. The house style lives in `references/style-guide.md`; the document skeleton lives in `assets/proposal-template.md`. Read both before writing.

## Workflow

### 1. Build a fact sheet before writing anything

Read the whole brief and pull out, in a scratch list:

- **Client**: organisation, contact name/role, who signs off.
- **Problem** in the client's own words, and the business outcome they care about (revenue, time saved, risk reduced).
- **Requirements**: must-haves vs nice-to-haves. Quote the brief where it is explicit.
- **Constraints**: deadline, budget signals, tech stack, compliance, languages, integrations.
- **Unknowns**: anything the estimate depends on that the brief does not answer.

Why: proposals go wrong when the writer fills gaps with invented facts. Every claim in the final document should trace back to the brief or be labelled as an assumption.

### 2. Shape the scope

- Group work into 2-5 **phases** (e.g. Discovery, Build, Launch, Support), each with concrete **deliverables** a client can check ("Booking flow live on the website", not "development work").
- Write an explicit **Out of scope** list. The items most likely to cause disputes are integrations, content creation, data migration, ongoing support and extra revision rounds - mention each one the brief touches.
- If the brief is too vague to scope responsibly, still produce the proposal but make the first phase a paid or short discovery, and move the uncertain work into an option.

### 3. Estimate and price

Follow `references/pricing-guidance.md`. In short: estimate effort per deliverable in days (best case / likely), multiply by the day rate from the style guide, and add the contingency the style guide specifies as its own line. When the budget is unclear or the scope has a natural "lite" version, offer **three options** (Essential / Recommended / Complete) and mark one as recommended. Never let the line items and the total disagree - add them up and check.

### 4. Plan the timeline

Use weeks, not dates, unless the brief gives a fixed start. Show milestones, what the client must provide and when (content, access, feedback), and how client delays move the plan. If there is a hard deadline, say plainly whether it is achievable and what it would take.

### 5. Write it in house style

Fill `assets/proposal-template.md` section by section. Apply the voice rules in `references/style-guide.md` (plain English, "you/we", short paragraphs, no hype words). Use the client's vocabulary for their domain. Keep it skimmable: a decision-maker should get the gist from the summary, the pricing table and the timeline alone.

### 6. Self-check before handing over

Go through this list and fix anything that fails:

- [ ] Every requirement marked must-have in the brief appears in scope or is explicitly out of scope with a reason.
- [ ] Pricing table rows sum to the stated totals; currency and tax treatment are stated.
- [ ] Each assumption is something the client can confirm or correct.
- [ ] Timeline phases match the scope phases and the deliverables.
- [ ] No placeholder text (`{{...}}`, "TBD", "lorem") remains, except values the user must supply, which are listed in Open questions.
- [ ] Nothing is promised that the brief did not ask for and the team did not price.

### 7. Deliver

Return, in this order:

1. The proposal as one Markdown document (save it as `proposal-<client-slug>.md` when files can be written).
2. A cover email of at most 120 words that names the recommended option, the total and the one decision you need from the client.
3. **Open questions for the team** - unknowns that changed the estimate and anything you assumed on the team's behalf (e.g. day rate, availability).

## Adapting to the team

The style guide ships with example house details for a fictional studio. If those example values (studio name, rates, payment terms) are still in place when the user asks for a real proposal, use them but list "Confirm house details in the style guide" as the first open question. Teams customise the skill by editing `references/style-guide.md` and `assets/proposal-template.md` - not this file.
