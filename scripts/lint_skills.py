#!/usr/bin/env python3
"""Lint every skill in skills/ (or the given skill folders).

Checks frontmatter (required fields, allowed keys, name format, description
length and trigger wording), body size, that every file referenced from
SKILL.md exists, that bundled files are referenced, that Python scripts
compile, and the upload limits of Claude.ai / the Skills API.

Usage:
  python scripts/lint_skills.py                # all skills, warnings allowed
  python scripts/lint_skills.py --strict       # warnings fail too (CI)
  python scripts/lint_skills.py skills/foo     # one skill
  python scripts/lint_skills.py --json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required: pip install -r requirements-dev.txt")

ROOT = Path(__file__).resolve().parent.parent
ALLOWED_KEYS = {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}
RESERVED_WORDS = ("anthropic", "claude")
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DESCRIPTION_MAX = 1024
DESCRIPTION_MIN_RECOMMENDED = 150
BODY_MAX_LINES = 500
MAX_TOTAL_BYTES = 30 * 1024 * 1024
TRIGGER_HINT = re.compile(r"\b(use (this|it|when)|whenever|when the user)\b", re.I)
LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
PATH_RE = re.compile(r"(?<![\w.-])((?:scripts|references|assets)/[\w./-]*[\w-]\.[A-Za-z0-9]+)")
IGNORED_FILES = {".DS_Store"}
IGNORED_DIRS = {"__pycache__", "node_modules", "evals"}


@dataclass
class Result:
    skill: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: dict = field(default_factory=dict)


def split_frontmatter(text: str) -> tuple[str | None, str]:
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---", 4)
    if end < 0:
        return None, text
    after = text.find("\n", end + 4)
    return text[4:end], text[after + 1:] if after >= 0 else ""


def bundled_files(skill_dir: Path) -> list[Path]:
    files = []
    for path in skill_dir.rglob("*"):
        rel = path.relative_to(skill_dir)
        if path.is_file() and path.name not in IGNORED_FILES and not any(p in IGNORED_DIRS for p in rel.parts) and path.suffix != ".pyc":
            files.append(path)
    return files


def lint_skill(skill_dir: Path) -> Result:
    result = Result(skill=skill_dir.name)
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        result.errors.append("SKILL.md not found.")
        return result

    nested = [p for p in skill_dir.rglob("SKILL.md") if p != skill_md and not any(x in IGNORED_DIRS for x in p.relative_to(skill_dir).parts)]
    if nested:
        result.errors.append(f"Extra SKILL.md files (uploads accept exactly one): {', '.join(str(p.relative_to(skill_dir)) for p in nested)}")

    text = skill_md.read_text(encoding="utf-8")
    raw_frontmatter, body = split_frontmatter(text)
    if raw_frontmatter is None:
        result.errors.append("SKILL.md must start with YAML frontmatter delimited by '---' lines.")
        return result
    try:
        meta = yaml.safe_load(raw_frontmatter)
    except yaml.YAMLError as exc:
        result.errors.append(f"Frontmatter is not valid YAML: {exc}")
        return result
    if not isinstance(meta, dict):
        result.errors.append("Frontmatter must be a YAML mapping.")
        return result

    unknown = set(meta) - ALLOWED_KEYS
    if unknown:
        result.errors.append(f"Unknown frontmatter key(s): {', '.join(sorted(unknown))}. Allowed: {', '.join(sorted(ALLOWED_KEYS))}.")

    name = meta.get("name")
    if not isinstance(name, str) or not name.strip():
        result.errors.append("Missing 'name'.")
    else:
        if not NAME_RE.match(name):
            result.errors.append(f"name '{name}' must be kebab-case (lowercase letters, digits, single hyphens).")
        if len(name) > 64:
            result.errors.append(f"name is {len(name)} characters (max 64).")
        if any(word in name for word in RESERVED_WORDS):
            result.errors.append(f"name '{name}' contains a reserved word ({', '.join(RESERVED_WORDS)}).")
        if name != skill_dir.name:
            result.errors.append(f"name '{name}' does not match folder name '{skill_dir.name}'.")

    description = meta.get("description")
    if not isinstance(description, str) or not description.strip():
        result.errors.append("Missing 'description'.")
    else:
        description = description.strip()
        result.info["description_chars"] = len(description)
        if len(description) > DESCRIPTION_MAX:
            result.errors.append(f"description is {len(description)} characters (max {DESCRIPTION_MAX}).")
        if "<" in description or ">" in description:
            result.errors.append("description must not contain angle brackets (< or >).")
        if len(description) < DESCRIPTION_MIN_RECOMMENDED:
            result.warnings.append(f"description is only {len(description)} characters; say what it does AND when to use it (aim for 300-900).")
        if not TRIGGER_HINT.search(description):
            result.warnings.append("description has no trigger guidance (e.g. 'Use this whenever ...').")

    compatibility = meta.get("compatibility")
    if compatibility is not None and (not isinstance(compatibility, str) or len(compatibility) > 500):
        result.errors.append("compatibility must be a string of at most 500 characters.")
    if "license" not in meta:
        result.warnings.append("No 'license' in frontmatter.")
    if not isinstance(meta.get("metadata", {}), dict):
        result.errors.append("metadata must be a mapping.")

    body_lines = body.strip().splitlines()
    result.info["body_lines"] = len(body_lines)
    if not body_lines:
        result.errors.append("SKILL.md has no instructions after the frontmatter.")
    elif len(body_lines) > BODY_MAX_LINES:
        result.warnings.append(f"SKILL.md body is {len(body_lines)} lines; keep it under {BODY_MAX_LINES} and move detail to references/.")
    if not re.search(r"^#{1,3} ", body, re.M):
        result.warnings.append("SKILL.md body has no Markdown headings.")

    # Referenced files must exist; bundled files should be referenced.
    referenced: set[str] = set()
    for target in LINK_RE.findall(body):
        if re.match(r"^(https?:|mailto:|#)", target):
            continue
        referenced.add(target.split("#")[0])
    referenced.update(PATH_RE.findall(body))
    for rel in sorted(referenced):
        if not (skill_dir / rel).exists():
            result.errors.append(f"Referenced file does not exist: {rel}")

    files = bundled_files(skill_dir)
    result.info["files"] = len(files)
    total = sum(p.stat().st_size for p in files)
    result.info["bytes"] = total
    if total > MAX_TOTAL_BYTES:
        result.errors.append(f"Skill is {total / 1e6:.1f} MB; uploads must be under 30 MB.")

    # Files can also be referenced from other bundled markdown files (one level of indirection).
    reachable = set(referenced)
    for rel in list(referenced):
        path = skill_dir / rel
        if path.suffix == ".md" and path.is_file():
            reachable.update(PATH_RE.findall(path.read_text(encoding="utf-8")))
    for path in files:
        rel = path.relative_to(skill_dir).as_posix()
        if rel == "SKILL.md":
            continue
        if rel not in reachable:
            result.warnings.append(f"Bundled file is never referenced from SKILL.md: {rel}")
        if path.suffix == ".py":
            try:
                compile(path.read_text(encoding="utf-8"), str(path), "exec")  # syntax check without writing .pyc files
            except SyntaxError as exc:
                result.errors.append(f"{rel} does not compile: line {exc.lineno}: {exc.msg}")
            if not path.read_text(encoding="utf-8").startswith("#!"):
                result.warnings.append(f"{rel} has no shebang line.")
    return result


def discover(paths: list[str]) -> list[Path]:
    if paths:
        return [Path(p).resolve() for p in paths]
    return sorted(p for p in (ROOT / "skills").iterdir() if p.is_dir() and not p.name.startswith("."))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("skills", nargs="*", help="skill folders (default: every folder in skills/)")
    parser.add_argument("--strict", action="store_true", help="treat warnings as errors")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    results = [lint_skill(d) for d in discover(args.skills)]
    names = [r.skill for r in results]
    for dup in {n for n in names if names.count(n) > 1}:
        for r in results:
            if r.skill == dup:
                r.errors.append("Duplicate skill name.")

    failed = [r for r in results if r.errors or (args.strict and r.warnings)]
    if args.json:
        print(json.dumps([r.__dict__ for r in results], indent=2))
    else:
        for r in results:
            status = "FAIL" if r in failed else "ok  "
            detail = f"description {r.info.get('description_chars', '?')} chars, body {r.info.get('body_lines', '?')} lines, {r.info.get('files', '?')} files"
            print(f"[{status}] {r.skill:<24} {detail}")
            for e in r.errors:
                print(f"        error:   {e}")
            for w in r.warnings:
                print(f"        warning: {w}")
        total_w = sum(len(r.warnings) for r in results)
        total_e = sum(len(r.errors) for r in results)
        print(f"\n{len(results)} skill(s) checked: {len(results) - len(failed)} passed, {len(failed)} failed "
              f"({total_e} error(s), {total_w} warning(s){', strict mode' if args.strict else ''}).")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
