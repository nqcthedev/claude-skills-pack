---
name: code-review-checklist
description: Review a git diff, branch or pull request against a configurable team checklist covering security, correctness, tests, performance and maintainability, and return a verdict with severity-ranked findings (file and line, why it matters, suggested fix) plus a checklist coverage table. Includes a helper script that collects the diff, commit list, change stats and risk flags such as possible secrets, debug statements and untested source changes. Use this whenever the user asks to review code, a PR or MR, a branch, staged changes or a patch, asks "is this ready to merge", "anything wrong with my changes" or wants a pre-merge checklist, even if no checklist is mentioned.
license: MIT
compatibility: Needs git and Python 3.9+ (standard library only) for the helper script; works on any language.
metadata:
  version: "1.0.0"
  author: Cuong Nguyen
---

# Code review checklist

Review changes the way a careful senior engineer would: read the actual code, rank problems by impact, give fixes that can be applied, and be explicit about what could not be verified from the diff alone.

## Workflow

### 1. Gather the change

Run the helper from the repository root (it never modifies the repo):

```bash
python <skill-dir>/scripts/gather_diff.py --base main --out .review
```

Useful variants: `--staged` (staged changes only), `--working` (uncommitted changes), `--base origin/develop`, `--context 10` (more surrounding lines). It writes:

- `.review/diff.patch` - the unified diff to review.
- `.review/summary.json` - files with status, language, +/- counts, test/generated/lockfile flags, commit list, and **risk flags** (possible secrets, debug statements, new TODOs, migrations, dependency or CI changes, large files, source changed without tests).
- It prints a short summary and which checklist to use.

If the user pasted a diff or the PR is not in a local repository, skip the script and review the pasted diff directly; note that the automated risk scan did not run.

### 2. Choose the checklist

Use the first that exists:

1. The path the user gives.
2. `.code-review-checklist.md` in the repository root (the script reports it as `checklist_path`).
3. `references/default-checklist.md` in this skill.

Teams customise reviews by committing their own `.code-review-checklist.md` in the same format (item ids such as `SEC-1`, grouped by section, each item one checkable sentence). Respect any section a team marks as not applicable.

### 3. Review

- Start with the risk flags from `summary.json` - each one must be either confirmed as a finding or dismissed with a reason.
- Read every changed hunk. When a hunk's correctness depends on code outside the diff (callers, schema, config), open those files instead of guessing. If you cannot access them, say what you would need to check.
- Check each checklist item against the change. Every finding cites the checklist item id it violates.
- Prefer few, important findings over many cosmetic ones. Style issues that a formatter or linter would catch are at most `nit`.

Severity scale:

| Severity | Meaning | Merge? |
|---|---|---|
| `blocker` | Security hole, data loss, crash on a main path, broken build, secret in code | Must fix before merge |
| `major` | Wrong behaviour in a realistic case, missing tests for new logic, significant performance problem | Should fix before merge |
| `minor` | Edge case, unclear naming, missing docs, small inefficiency | Fix now or ticket it |
| `nit` | Preference or polish | Optional |

### 4. Write the review

Use `assets/review-template.md`. The verdict is **Request changes** if there is any blocker or major finding, **Approve with comments** if only minor/nit, otherwise **Approve**. For each finding give: severity, `path:line` (line numbers from the new file), checklist id, what is wrong, why it matters (concrete consequence), and a suggested fix - a code snippet when it is short. Then fill the checklist coverage table with one status per item: `pass`, `issue` (link to finding), `n/a`, or `not verifiable` (explain briefly). End with what was done well, if anything genuinely was - one or two specific points, no filler.

### 5. Hand over

Show the review. If the user asked for it as a file, save `REVIEW.md` (not inside `.review/`, which is scratch output and should be git-ignored). Do not commit, push or post comments unless the user asks.
