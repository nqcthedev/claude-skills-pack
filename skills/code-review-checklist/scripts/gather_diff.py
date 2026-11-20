#!/usr/bin/env python3
"""Collect a git diff plus stats and risk flags for a code review.

Usage (run inside the repository):
  python gather_diff.py [--base main] [--out .review]   # branch vs merge-base with base
  python gather_diff.py --staged                         # staged changes only
  python gather_diff.py --working                        # all uncommitted changes vs HEAD

Writes <out>/diff.patch and <out>/summary.json and prints a short summary.
Read-only: never changes the repository. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CHECKLIST = SKILL_DIR / "references" / "default-checklist.md"
REPO_CHECKLIST = ".code-review-checklist.md"

LANGUAGES = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript", ".go": "Go", ".rs": "Rust", ".java": "Java", ".kt": "Kotlin",
    ".rb": "Ruby", ".php": "PHP", ".cs": "C#", ".swift": "Swift", ".c": "C", ".h": "C", ".cpp": "C++",
    ".sql": "SQL", ".sh": "Shell", ".html": "HTML", ".css": "CSS", ".scss": "SCSS", ".vue": "Vue",
    ".svelte": "Svelte", ".md": "Markdown", ".yml": "YAML", ".yaml": "YAML", ".json": "JSON", ".toml": "TOML",
}
DOC_OR_CONFIG = {"Markdown", "YAML", "JSON", "TOML"}
LOCKFILES = {"package-lock.json", "pnpm-lock.yaml", "yarn.lock", "poetry.lock", "Pipfile.lock", "Cargo.lock",
             "go.sum", "composer.lock", "Gemfile.lock", "uv.lock", "bun.lockb"}
MANIFESTS = {"package.json", "requirements.txt", "pyproject.toml", "Pipfile", "go.mod", "Cargo.toml", "Gemfile",
             "composer.json", "pom.xml", "build.gradle", "build.gradle.kts", "setup.py", "setup.cfg"}
CI_PATTERNS = (r"^\.github/workflows/", r"^\.gitlab-ci\.yml$", r"(^|/)Jenkinsfile$", r"(^|/)Dockerfile", r"^\.circleci/")
TEST_PATTERNS = (r"(^|/)(tests?|__tests__|spec|specs)/", r"(^|/)test_[^/]+\.py$", r"_test\.(py|go)$", r"\.(test|spec)\.[cm]?[jt]sx?$",
                 r"Test\.(java|kt|cs)$")
GENERATED_PATTERNS = (r"(^|/)(dist|build|vendor|node_modules)/", r"\.min\.(js|css)$", r"\.generated\.", r"_pb2\.py$")

SECRET_PATTERNS = [
    ("aws_access_key", r"AKIA[0-9A-Z]{16}"),
    ("private_key", r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    ("github_token", r"gh[pousr]_[A-Za-z0-9]{36,}"),
    ("slack_token", r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    ("stripe_live_key", r"[sr]k_live_[A-Za-z0-9]{16,}"),
    ("google_api_key", r"AIza[0-9A-Za-z_-]{35}"),
    ("jwt", r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    ("hardcoded_credential", r"(?i)\b[\w-]*(api[_-]?key|secret|token|passw(or)?d|pwd)[\w-]*\b\s*[:=]\s*['\"][^'\"\s]{8,}['\"]"),
]
LINE_PATTERNS = [
    ("debug_statement", r"\bconsole\.(log|debug|trace)\(|\bdebugger;|\bpdb\.set_trace\(|\bbreakpoint\(\)|\bvar_dump\(|\bprint_r\(|System\.out\.println\("),
    ("todo_added", r"\b(TODO|FIXME|XXX|HACK)\b"),
    ("weak_random_or_hash", r"\brandom\.(random|randint|choice)\(|\bMath\.random\(|\bmd5\(|\bsha1\(|hashlib\.(md5|sha1)\("),
    ("possible_sql_injection", r"(?i)(\bf\"[^\"]*\b(select|insert|update|delete)\b[^\"]*\{|\bf'[^']*\b(select|insert|update|delete)\b[^']*\{|[\"'][^\"']*\b(select|insert|update|delete)\b[^\"']*[\"']\s*(\+|%|\.format\())"),
    ("shell_injection_risk", r"subprocess\.\w+\([^)]*shell\s*=\s*True|\bos\.system\(|child_process\.exec\("),
]


def git(repo: Path, *args: str, check: bool = True) -> str:
    proc = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def default_base(repo: Path) -> str:
    head = git(repo, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD", check=False).strip()
    if head:
        return head
    for candidate in ("main", "master", "develop"):
        if git(repo, "rev-parse", "--verify", "--quiet", candidate, check=False).strip():
            return candidate
    return "HEAD~1"


def matches(path: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(p, path) for p in patterns)


def added_lines(patch: str):
    """Yield (path, new_line_number, text) for every added line in a unified diff."""
    path = None
    line_no = 0
    for raw in patch.splitlines():
        if raw.startswith("+++ "):
            target = raw[4:].strip()
            path = None if target == "/dev/null" else re.sub(r"^b/", "", target)
            continue
        if raw.startswith("@@"):
            m = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", raw)
            line_no = int(m.group(1)) if m else 0
            continue
        if path is None or raw.startswith(("--- ", "diff --git", "index ", "\\ ")):
            continue
        if raw.startswith("+"):
            yield path, line_no, raw[1:]
            line_no += 1
        elif raw.startswith(" "):
            line_no += 1


def collect(repo: Path, mode: str, base: str | None, context: int) -> dict:
    if mode == "staged":
        diff_args = ["--cached"]
        label = "staged changes"
        commits: list[dict] = []
    elif mode == "working":
        diff_args = ["HEAD"]
        label = "uncommitted changes vs HEAD"
        commits = []
    else:
        base = base or default_base(repo)
        merge_base = git(repo, "merge-base", base, "HEAD").strip()
        diff_args = [merge_base, "HEAD"]
        label = f"HEAD vs merge-base with {base} ({merge_base[:10]})"
        log = git(repo, "log", "--no-merges", "--format=%h%x09%an%x09%s", f"{merge_base}..HEAD")
        commits = [dict(zip(("sha", "author", "subject"), line.split("\t", 2))) for line in log.splitlines() if line]

    patch = git(repo, "diff", "-M", f"--unified={context}", *diff_args)
    numstat = git(repo, "diff", "-M", "--numstat", *diff_args)
    name_status = git(repo, "diff", "-M", "--name-status", *diff_args)

    statuses: dict[str, str] = {}
    for line in name_status.splitlines():
        parts = line.split("\t")
        code = parts[0][0]
        statuses[parts[-1]] = {"A": "added", "D": "deleted", "M": "modified", "R": "renamed", "C": "copied", "T": "type-changed"}.get(code, code)

    files = []
    for line in numstat.splitlines():
        adds, dels, *rest = line.split("\t")
        path = rest[-1]
        if " => " in path:  # rename in numstat: a/{x => y}/b or x => y
            path = re.sub(r"\{[^{}]* => ([^{}]*)\}", r"\1", path)
            path = path.split(" => ")[-1]
            path = path.replace("//", "/")
        name = PurePosixPath(path).name
        binary = adds == "-"
        files.append({
            "path": path,
            "status": statuses.get(path, "modified"),
            "language": LANGUAGES.get(PurePosixPath(path).suffix.lower(), "Other"),
            "additions": 0 if binary else int(adds),
            "deletions": 0 if binary else int(dels),
            "binary": binary,
            "is_test": matches(path, TEST_PATTERNS),
            "is_generated": name in LOCKFILES or matches(path, GENERATED_PATTERNS),
        })

    flags: list[dict] = []

    def flag(kind: str, path: str, line: int | None, detail: str) -> None:
        flags.append({"type": kind, "path": path, "line": line, "detail": detail[:160]})

    for path, line_no, text in added_lines(patch):
        if PurePosixPath(path).name in LOCKFILES:
            continue
        for kind, pattern in SECRET_PATTERNS:
            if re.search(pattern, text):
                flag("possible_secret", path, line_no, f"{kind}: {text.strip()}")
                break
        for kind, pattern in LINE_PATTERNS:
            if re.search(pattern, text):
                flag(kind, path, line_no, text.strip())
        if path.endswith(".py") and re.match(r"\s*print\(", text) and not matches(path, TEST_PATTERNS) \
                and not re.search(r"(^|/)(scripts?|bin|cli|tools)/|(^|/)(manage|cli|__main__)\.py$", path):
            flag("debug_statement", path, line_no, text.strip())

    for f in files:
        name = PurePosixPath(f["path"]).name
        if re.search(r"(^|/)migrations?/|\.sql$", f["path"]):
            flag("migration", f["path"], None, "Database migration or SQL file changed")
        if name in MANIFESTS:
            flag("dependency_change", f["path"], None, "Dependency manifest changed")
        if matches(f["path"], CI_PATTERNS):
            flag("ci_or_build_change", f["path"], None, "CI/CD or container build config changed")
        if f["additions"] + f["deletions"] > 500 and not f["is_generated"]:
            flag("large_change", f["path"], None, f"{f['additions'] + f['deletions']} lines changed in one file")
        if f["binary"]:
            flag("binary_file", f["path"], None, "Binary file changed")

    source = [f for f in files if not f["is_test"] and not f["is_generated"] and f["language"] not in DOC_OR_CONFIG | {"Other"} and f["status"] != "deleted"]
    tests = [f for f in files if f["is_test"]]
    if source and not tests:
        flag("source_without_tests", source[0]["path"], None, f"{len(source)} source file(s) changed, no test files changed")

    checklist = repo / REPO_CHECKLIST
    return {
        "range": label,
        "mode": mode,
        "base": base,
        "checklist_path": str(checklist if checklist.exists() else DEFAULT_CHECKLIST),
        "totals": {
            "files": len(files),
            "additions": sum(f["additions"] for f in files),
            "deletions": sum(f["deletions"] for f in files),
            "source_files": len(source),
            "test_files": len(tests),
        },
        "languages": sorted({f["language"] for f in files}),
        "commits": commits,
        "files": files,
        "risk_flags": flags,
        "patch_bytes": len(patch.encode()),
    }, patch


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--staged", action="store_true", help="review staged changes only")
    group.add_argument("--working", action="store_true", help="review all uncommitted changes vs HEAD")
    parser.add_argument("--base", help="base branch/ref for branch mode (default: origin/HEAD, main, master or develop)")
    parser.add_argument("--repo", default=".", help="repository path (default: current directory)")
    parser.add_argument("--out", default=".review", help="output directory (default: .review)")
    parser.add_argument("--context", type=int, default=5, help="lines of context in the patch (default: 5)")
    parser.add_argument("--max-patch-kb", type=int, default=800, help="truncate diff.patch beyond this size (default: 800)")
    args = parser.parse_args(argv)

    repo = Path(args.repo).resolve()
    try:
        root = git(repo, "rev-parse", "--show-toplevel").strip()
    except (RuntimeError, FileNotFoundError) as exc:
        print(f"error: not a git repository (or git missing): {exc}", file=sys.stderr)
        return 2
    repo = Path(root)
    mode = "staged" if args.staged else "working" if args.working else "branch"
    try:
        summary, patch = collect(repo, mode, args.base, args.context)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    out = Path(args.out)
    if not out.is_absolute():
        out = repo / out
    out.mkdir(parents=True, exist_ok=True)
    limit = args.max_patch_kb * 1024
    if len(patch.encode()) > limit:
        patch = patch.encode()[:limit].decode(errors="ignore") + "\n\n[diff truncated - review the remaining files individually]\n"
        summary["truncated"] = True
    (out / "diff.patch").write_text(patch, encoding="utf-8")
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    t = summary["totals"]
    print(f"Range: {summary['range']}")
    print(f"Files: {t['files']} (+{t['additions']} / -{t['deletions']}), source {t['source_files']}, tests {t['test_files']}; "
          f"commits: {len(summary['commits'])}; languages: {', '.join(summary['languages']) or '-'}")
    print(f"Checklist: {summary['checklist_path']}")
    if summary["risk_flags"]:
        print(f"Risk flags ({len(summary['risk_flags'])}) - confirm or dismiss each:")
        for f in summary["risk_flags"]:
            where = f"{f['path']}:{f['line']}" if f["line"] else f["path"]
            print(f"  - {f['type']}: {where} - {f['detail']}")
    else:
        print("Risk flags: none")
    print(f"Wrote {out / 'diff.patch'} and {out / 'summary.json'}")
    if not t["files"]:
        print("Nothing to review: the diff is empty.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
