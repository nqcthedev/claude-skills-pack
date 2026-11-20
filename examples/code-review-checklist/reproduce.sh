#!/usr/bin/env bash
# Rebuilds the example pull request in a throwaway git repo and runs the
# skill's helper script on it, writing output/gather/{summary.json,diff.patch,stdout.txt}.
# Usage: bash examples/code-review-checklist/reproduce.sh
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACK="$(cd "$HERE/../.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

cp -r "$HERE/input/base/." "$WORK/"
cd "$WORK"
export GIT_AUTHOR_DATE="2026-12-14T10:00:00+07:00" GIT_COMMITTER_DATE="2026-12-14T10:00:00+07:00"
git init -q -b main
git -c user.name="Example Dev" -c user.email=dev@example.com add -A
git -c user.name="Example Dev" -c user.email=dev@example.com commit -qm "Booking API"
git checkout -qb feature/cancel-link
git apply "$HERE/input/cancel-link.patch"
git add -A
git -c user.name="Bao Dang" -c user.email=bao.dang@northbeam.example commit -qm "Add cancel-by-link to SMS reminders"

mkdir -p "$HERE/output/gather"
python3 "$PACK/skills/code-review-checklist/scripts/gather_diff.py" --base main --out .review \
  | sed -e "s#$WORK/##g" -e "s#$PACK/##g" > "$HERE/output/gather/stdout.txt"
# Paths are made relative so the recorded output is machine-independent.
python3 - "$WORK/.review/summary.json" "$HERE/output/gather/summary.json" "$PACK" <<'PY'
import json, sys
data = json.load(open(sys.argv[1]))
data["checklist_path"] = data["checklist_path"].replace(sys.argv[3] + "/", "")
json.dump(data, open(sys.argv[2], "w"), indent=2)
open(sys.argv[2], "a").write("\n")
PY
cp .review/diff.patch "$HERE/output/gather/diff.patch"
cat "$HERE/output/gather/stdout.txt"
