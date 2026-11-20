# Using the web-insights MCP tools for a brief

**web-insights-mcp** (a companion open-source project) is an MCP server with read-only web research tools. When connected, its tools may appear with a server prefix (for example `mcp__web-insights__fetch_page`). Calls below show the arguments to pass.

## Recipe

1. **Read each competitor** - content, headings, word count:

   ```json
   { "tool": "fetch_page", "arguments": { "url": "<competitor>", "max_chars": 12000 } }
   ```

   Use `"mode": "full"` if the result looks cut off (landing pages, listicles with cards).

2. **Outline and schema per page**:

   ```json
   { "tool": "extract_structured", "arguments": { "url": "<competitor>", "include": ["headings", "json_ld", "meta"] } }
   ```

3. **Gap analysis** - compare our page (or the strongest competitor) with each other page:

   ```json
   { "tool": "compare_pages", "arguments": { "url_a": "<our page>", "url_b": "<competitor>" } }
   ```

   `differences.headings.onlyInB` = sub-topics the competitor covers and we do not. `differences.phrases.onlyInB` = observed terms worth covering. `observations` gives a plain-English summary.

4. **Audit our page** (refresh case):

   ```json
   { "tool": "seo_audit", "arguments": { "url": "<our page>" } }
   ```

   Carry `error` and `warning` issues into the brief's "Technical fixes" section.

## Reading the results

- `wordCount` is main-content words (navigation and footer removed) - use it for the length target.
- `topPhrases` are frequency-based two-word terms from the page text: evidence of what the page talks about, not search demand.
- `structuredDataTypes` lists schema.org types found in JSON-LD; recommend only types whose content the new page will actually show.
- If a tool returns an error (blocked, timeout, non-HTML), note it in the research log and continue with the remaining pages.
