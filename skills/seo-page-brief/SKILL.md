---
name: seo-page-brief
description: Create an SEO content brief for a new or existing page from a target keyword and the competitor pages that rank for it - search intent, recommended title, meta description, H1 and slug, a section-by-section outline, must-cover topics, content gaps, target length, FAQs, internal links, schema markup and a competitor comparison table built from real page data. Uses the web-insights MCP tools (fetch_page, compare_pages, extract_structured, seo_audit) when they are connected, and falls back to other fetch tools or pasted content. Use this whenever the user asks for a content brief, SEO brief, article outline for ranking, "what should this page cover to rank for X", a content gap or competitor content analysis, or wants to refresh a page that lost rankings.
license: MIT
compatibility: Works best with the web-insights MCP server connected; otherwise needs any web fetch tool or user-pasted page content.
metadata:
  version: "1.0.0"
  author: Cuong Nguyen
---

# SEO page brief

Give a writer everything they need to produce a page that deserves to rank: what the searcher wants, what the current top pages already cover, where they fall short, and exactly how this page will be better. The brief must be grounded in fetched page data, never in guesses about what competitors "probably" say.

## Inputs

- **Target keyword** (required) and market/language if not English.
- **Competitor URLs** - 2-5 pages that currently rank. If the user has none and no search tool is available, ask for them; do not invent URLs.
- **Our page** (optional) - the URL to refresh, or the site for internal links.
- Audience, business goal and conversion action, if known.

## Workflow

### 1. Collect page data

Pick the best available route and say which one you used in the brief:

**A. web-insights MCP connected** (tools named `fetch_page`, `compare_pages`, `extract_structured`, `seo_audit`, possibly prefixed with the server name). Follow the recipes in `references/web-insights-recipes.md`: fetch each competitor, extract headings and structured data, run `compare_pages` between our page (or the strongest competitor) and each other page, and audit our page if it exists.

**B. Another fetch tool** (built-in web fetch, browser). Fetch each page and record title, meta description, H1, H2/H3 outline, approximate word count, FAQ presence, schema types if visible, and the main claims/data points.

**C. No tools.** Ask the user to paste each competitor's content (or export from their SEO tool). Work only from what is pasted.

Keep a short research log: URL, retrieval route, date, word count, headings. Put it in the brief's appendix so editors can trust and re-check it.

### 2. Analyse

1. **Search intent**: informational, commercial investigation, transactional or navigational - judged from what the ranking pages are (guides vs product pages vs comparisons). The page type must match the dominant intent.
2. **Consensus topics**: sub-topics covered by most competitors. These are table stakes - list them as must-cover.
3. **Gaps**: useful questions only one or none of the competitors answer well (missing steps, no numbers, no troubleshooting, outdated info, no visuals, no FAQ). These are how the page wins.
4. **Format signals**: median and range of word count, use of tables, step lists, images/video, FAQ blocks, schema types (FAQPage, HowTo, Recipe, Product...).
5. **Our page** (refresh case): what it already covers, its SEO audit issues, and what to keep.

Be honest about evidence: keyword phrases found on competitor pages are "observed terms", not search volume. Never state search volume, difficulty or rankings unless the user supplied them or a connected tool returned them.

### 3. Write the brief

Fill `assets/brief-template.md`. Requirements:

- **Title** under 60 characters with the keyword near the start; **meta description** 140-155 characters with a reason to click; **slug** short, lowercase, hyphenated.
- **Outline**: H2/H3 structure in reading order. Under each heading: what to say, which gap it fills or consensus topic it covers, and any data, example or visual to include.
- **Target length** as a range anchored to the competitor median (a page should be as long as it needs to be to beat them on completeness, not padded).
- **FAQs** from real questions that appear in competitor headings or the user's input, answered in 1-2 sentences each.
- **Internal links**: from our site where known; otherwise list "link targets to create or confirm".
- **Schema**: recommend types that match visible content only.
- **Competitor table** with the actual numbers collected.

### 4. Quality check

- [ ] Every competitor fact in the brief traces to the research log.
- [ ] Title and meta lengths counted, not estimated.
- [ ] The outline covers all consensus topics and at least two concrete gaps.
- [ ] No invented search volumes, rankings or statistics.
- [ ] The brief states the data route used (A, B or C) and the retrieval date.

### 5. Hand over

Deliver the brief as one Markdown document (save as `brief-<keyword-slug>.md` when files can be written). Mention in two or three lines what will make this page better than the current results.
