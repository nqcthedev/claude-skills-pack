#!/usr/bin/env python3
"""Zip each skill into dist/<skill>.zip for Claude.ai upload or the Skills API.

Each archive contains a single top-level folder named after the skill with
SKILL.md at its root. Skills are linted first; packaging stops on errors.

Usage:
  python scripts/package_skills.py              # all skills
  python scripts/package_skills.py meeting-to-tasks
"""
from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lint_skills import ROOT, bundled_files, lint_skill  # noqa: E402


def package(skill_dir: Path, dist: Path) -> Path:
    dist.mkdir(parents=True, exist_ok=True)
    target = dist / f"{skill_dir.name}.zip"
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(bundled_files(skill_dir)):
            info = zipfile.ZipInfo(f"{skill_dir.name}/{path.relative_to(skill_dir).as_posix()}", date_time=(2026, 1, 1, 0, 0, 0))
            info.external_attr = (0o755 if path.suffix in {".py", ".sh"} else 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, path.read_bytes())
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("skills", nargs="*", help="skill names (default: all)")
    parser.add_argument("--dist", default=str(ROOT / "dist"), help="output directory (default: dist/)")
    args = parser.parse_args(argv)
    dirs = [ROOT / "skills" / n for n in args.skills] or sorted(p for p in (ROOT / "skills").iterdir() if p.is_dir())
    for skill_dir in dirs:
        result = lint_skill(skill_dir)
        if result.errors:
            print(f"{skill_dir.name}: not packaged, lint errors: {'; '.join(result.errors)}", file=sys.stderr)
            return 1
        target = package(skill_dir, Path(args.dist))
        with zipfile.ZipFile(target) as zf:
            count = len(zf.namelist())
        print(f"{target.relative_to(ROOT) if target.is_relative_to(ROOT) else target}  ({count} files, {target.stat().st_size / 1024:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
