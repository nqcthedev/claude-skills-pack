// Renders README screenshots of the real example outputs (deviceScaleFactor 2).
// Needs the dev dependency `marked` (pnpm install) and Playwright with Chromium.
// Usage: pnpm screenshots
import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { marked } from "marked";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const read = (p) => readFileSync(join(ROOT, p), "utf8");
const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

/** Markdown between a heading (inclusive) and the next heading of the same or higher level. */
function section(md, heading) {
  const lines = md.split("\n");
  const start = lines.findIndex((l) => l.trim() === heading);
  if (start < 0) throw new Error(`heading not found: ${heading}`);
  const level = heading.match(/^#+/)[0].length;
  const next = lines.findIndex((l, i) => i > start && /^#+ /.test(l) && l.match(/^#+/)[0].length <= level);
  return lines.slice(start, next < 0 ? lines.length : next).join("\n");
}

const python = (args) => execFileSync("python3", args, { cwd: ROOT, encoding: "utf8" });

const css = `
*{box-sizing:border-box} body{margin:0;background:#eef1f6;font:15px/1.6 Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;color:#1d2330}
.wrap{padding:28px} .bar{display:flex;align-items:center;gap:12px;margin-bottom:16px}
.badge{font:600 12px/1 ui-monospace,Menlo,monospace;background:#1d2330;color:#fff;padding:7px 10px;border-radius:7px}
.flow{color:#5b6475;font-size:13.5px} .flow b{color:#1d2330}
.grid{display:grid;grid-template-columns:1fr;gap:16px;align-items:start} .two{grid-template-columns:1.25fr 1fr}
.doc{background:#fff;border:1px solid #dde2ea;border-radius:12px;padding:26px 32px;box-shadow:0 1px 2px rgba(20,30,50,.04)}
.doc h1{font-size:23px;margin:0 0 6px;letter-spacing:-.01em} .doc h2{font-size:18px;margin:22px 0 8px} .doc>*:nth-child(1),.doc .label+*{margin-top:0} .doc h3{font-size:15.5px;margin:18px 0 6px}
.doc p{margin:8px 0} .doc table{border-collapse:collapse;width:100%;font-size:13.5px;margin:10px 0}
.doc th,.doc td{border-bottom:1px solid #e6e9ef;padding:7px 9px;text-align:left;vertical-align:top} .doc th{background:#f6f8fb;font-weight:600}
.doc code{font:12.5px ui-monospace,Menlo,monospace;background:#f2f4f8;padding:1px 5px;border-radius:4px}
.doc pre{background:#f6f8fb;border:1px solid #e6e9ef;border-radius:8px;padding:12px 14px;overflow:hidden;white-space:pre-wrap}
.doc pre code{background:none;padding:0} .doc ul{padding-left:20px;margin:6px 0} .doc blockquote{margin:8px 0;padding:2px 14px;border-left:3px solid #c8d0dc;color:#4a5263}
.term{background:#11151d;color:#d7dde8;border-radius:12px;padding:18px 22px;font:13px/1.6 "JetBrains Mono",ui-monospace,Menlo,monospace;white-space:pre-wrap}
.term .ok{color:#4ade80} .term .bad{color:#fb7185} .term .dim{color:#7c8699} .term .cmd{color:#93c5fd}
.label{font:600 11.5px/1 Inter,system-ui,sans-serif;letter-spacing:.06em;text-transform:uppercase;color:#7a8396;margin:0 0 10px}`;

const page = (badge, flow, body) =>
  `<!doctype html><html><head><meta charset="utf-8"><style>${css}</style></head><body><div class="wrap">
  <div class="bar"><span class="badge">${badge}</span><span class="flow">${flow}</span></div>${body}</div></body></html>`;

const doc = (md, label) => `<div class="doc">${label ? `<div class="label">${label}</div>` : ""}${marked.parse(md)}</div>`;
const term = (text) =>
  `<div class="term">${esc(text)
    .replace(/^(\$ .*)$/gm, '<span class="cmd">$1</span>')
    .replace(/\b(PASS|OK|ok)\b/g, '<span class="ok">$1</span>')
    .replace(/\b(FAIL|FAILED)\b/g, '<span class="bad">$1</span>')}</div>`;

// --- real command output
const lint = python(["scripts/lint_skills.py", "--strict"]);
const unittestOut = execFileSync("bash", ["-c", "python3 -m unittest discover -s tests 2>&1 | tail -3"], { cwd: ROOT, encoding: "utf8" });
const validate = python([
  "skills/meeting-to-tasks/scripts/tasks_tool.py", "validate", "examples/meeting-to-tasks/output/tasks.json",
  "--transcript", "examples/meeting-to-tasks/input/transcript.txt",
]);
const voice = read("examples/brand-voice-writer/output/checker-final.txt");
const gather = read("examples/code-review-checklist/output/gather/stdout.txt");

const proposal = read("examples/client-proposal/output/proposal-brightsmile-dental.md");
const tasks = read("examples/meeting-to-tasks/output/tasks.md");
const review = read("examples/code-review-checklist/output/REVIEW.md");
const brief = read("examples/seo-page-brief/output/brief-cold-brew-ratio.md");
const linkedin = read("examples/brand-voice-writer/output/linkedin.md");

const views = {
  "lint-and-tests": page(
    "claude-skills-pack",
    "Every skill is linted in CI; helper scripts and example outputs are unit-tested",
    term(`$ python scripts/lint_skills.py --strict\n${lint}\n$ python -m unittest discover -s tests\n${unittestOut.trim()}`),
  ),
  "client-proposal": page(
    "client-proposal",
    "<b>Input:</b> client email brief &nbsp;→&nbsp; <b>Output:</b> proposal with 3 priced options",
    `<div class="grid">${doc(
      proposal.split("\n## What you told us")[0] + "\n\n" + section(proposal, "### At a glance"),
    )}</div>`,
  ),
  "meeting-to-tasks": page(
    "meeting-to-tasks",
    "<b>Input:</b> call transcript &nbsp;→&nbsp; <b>Output:</b> recap, tasks.json, Jira/Asana/Notion CSV",
    `<div class="grid">${doc(tasks.split("\n## Open questions")[0])}${term(`$ python scripts/tasks_tool.py validate tasks.json --transcript transcript.txt\n${validate}`)}</div>`,
  ),
  "code-review": page(
    "code-review-checklist",
    "<b>Input:</b> PR branch &nbsp;→&nbsp; <b>Output:</b> verdict, ranked findings, checklist coverage",
    `<div class="grid">${term(`$ python scripts/gather_diff.py --base main\n${gather}`)}${doc(review.split("\n### 4.")[0])}</div>`,
  ),
  "brand-voice": page(
    "brand-voice-writer",
    "<b>Input:</b> voice guide + brief &nbsp;→&nbsp; <b>Output:</b> on-brand copy, checked",
    `<div class="grid two">${doc(linkedin, "LinkedIn post (final)")}<div class="grid">${term(`$ python scripts/check_draft.py --guide voice-guide.md ...\n${voice}`)}${doc(
      section(read("examples/brand-voice-writer/output/voice-check.md"), "## Rubric scores").replace("## Rubric scores", "### Rubric scores"),
    )}</div></div>`,
  ),
  "seo-brief": page(
    "seo-page-brief",
    "<b>Input:</b> keyword + competitor pages via web-insights MCP &nbsp;→&nbsp; <b>Output:</b> content brief",
    `<div class="grid">${doc(brief.split("\n## Outline")[0])}</div>`,
  ),
};

const playwright = createRequire(import.meta.url)("playwright");
mkdirSync(join(ROOT, "docs/screenshots"), { recursive: true });
const browser = await playwright.chromium.launch();
const context = await browser.newContext({ viewport: { width: 1280, height: 400 }, deviceScaleFactor: 2 });
const tab = await context.newPage();
for (const [name, html] of Object.entries(views)) {
  await tab.setContent(html, { waitUntil: "load" });
  const path = join(ROOT, "docs/screenshots", `${name}.png`);
  await tab.screenshot({ path, fullPage: true });
  console.log(`docs/screenshots/${name}.png`);
}
await browser.close();
