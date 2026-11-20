#!/usr/bin/env python3
"""Validate meeting-to-tasks JSON and export it as tracker-ready CSV.

Usage:
  python tasks_tool.py validate tasks.json [--transcript transcript.txt]
  python tasks_tool.py export tasks.json --format jira|asana|notion|generic [-o out.csv]

Standard library only. Exit code 0 = valid, 1 = validation errors, 2 = usage/IO error.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from datetime import date
from pathlib import Path

ID_PATTERNS = {"decisions": r"^D\d+$", "action_items": r"^A\d+$", "open_questions": r"^Q\d+$"}
PRIORITIES = ("high", "medium", "low")
DUE_BASES = ("explicit", "inferred", "none")
STATUSES = ("todo", "in_progress", "done")
SOURCES = ("transcript", "notes", "chat")
UNASSIGNED = "Unassigned"


def _parse_date(value: object) -> date | None:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _normalise(text: str) -> str:
    text = text.lower().replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = text.replace("—", "-").replace("–", "-").replace("…", "...")
    return re.sub(r"\s+", " ", text).strip()


def _quote_in_source(quote: str, source_norm: str) -> bool:
    """True if the quote appears in the source, allowing '...' to elide words between fragments."""
    fragments = [f.strip(" .,") for f in re.split(r"\.\.\.|\[\.\.\.\]", _normalise(quote))]
    position = 0
    for fragment in (f for f in fragments if f):
        found = source_norm.find(fragment, position)
        if found < 0:
            return False
        position = found + len(fragment)
    return True


def validate(data: object, transcript: str | None = None) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for a parsed tasks.json document."""
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(data, dict):
        return ["Top level must be a JSON object."], warnings

    meeting = data.get("meeting")
    meeting_date = None
    attendee_names: set[str] = set()
    if not isinstance(meeting, dict):
        errors.append("`meeting` object is required.")
    else:
        if not isinstance(meeting.get("title"), str) or not meeting["title"].strip():
            errors.append("meeting.title is required.")
        meeting_date = _parse_date(meeting.get("date"))
        if meeting_date is None:
            errors.append(f"meeting.date must be YYYY-MM-DD, got {meeting.get('date')!r}.")
        if meeting.get("source") not in SOURCES:
            warnings.append(f"meeting.source should be one of {', '.join(SOURCES)}.")
        attendees = meeting.get("attendees")
        if not isinstance(attendees, list) or not attendees:
            errors.append("meeting.attendees must be a non-empty list.")
        else:
            for i, person in enumerate(attendees):
                name = person.get("name") if isinstance(person, dict) else None
                if not isinstance(name, str) or not name.strip():
                    errors.append(f"meeting.attendees[{i}].name is required.")
                elif name in attendee_names:
                    errors.append(f"Duplicate attendee name {name!r}.")
                else:
                    attendee_names.add(name)
                email = person.get("email") if isinstance(person, dict) else None
                if email is not None and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", str(email)):
                    errors.append(f"meeting.attendees[{i}].email {email!r} is not a valid email.")

    if not isinstance(data.get("summary"), str) or len(data.get("summary", "").strip()) < 20:
        errors.append("summary is required (at least one full sentence).")

    source_norm = _normalise(transcript) if transcript else None
    all_ids: set[str] = set()

    for section, pattern in ID_PATTERNS.items():
        items = data.get(section, [])
        if not isinstance(items, list):
            errors.append(f"`{section}` must be a list.")
            continue
        for i, item in enumerate(items):
            where = f"{section}[{i}]"
            if not isinstance(item, dict):
                errors.append(f"{where} must be an object.")
                continue
            item_id = item.get("id")
            if not isinstance(item_id, str) or not re.fullmatch(pattern, item_id):
                errors.append(f"{where}.id {item_id!r} must match {pattern}.")
            elif item_id in all_ids:
                errors.append(f"Duplicate id {item_id}.")
            else:
                all_ids.add(item_id)
                where = f"{item_id}"
            if section != "open_questions":
                quote = item.get("source_quote")
                if not isinstance(quote, str) or not quote.strip():
                    errors.append(f"{where}: source_quote is required (verbatim evidence from the meeting).")
                elif source_norm is not None and not _quote_in_source(quote, source_norm):
                    errors.append(f"{where}: source_quote not found in transcript: {quote[:70]!r}")

    for item in data.get("decisions", []) if isinstance(data.get("decisions"), list) else []:
        if isinstance(item, dict) and not str(item.get("decision", "")).strip():
            errors.append(f"{item.get('id')}: decision text is required.")

    actions = data.get("action_items", [])
    if not isinstance(actions, list):
        actions = []
    if not actions:
        warnings.append("No action items found - double-check the source.")
    action_ids = {a.get("id") for a in actions if isinstance(a, dict)}
    for item in actions:
        if not isinstance(item, dict):
            continue
        where = str(item.get("id"))
        title = item.get("title")
        if not isinstance(title, str) or not 3 <= len(title.strip()) <= 80:
            errors.append(f"{where}: title is required and must be 3-80 characters.")
        elif title.split()[0].lower() in {"the", "a", "an", "maybe", "possibly", "we", "someone"}:
            warnings.append(f"{where}: title should start with a verb ({title!r}).")
        owner = item.get("owner")
        if owner != UNASSIGNED and owner not in attendee_names:
            errors.append(f"{where}: owner {owner!r} is not an attendee (use an attendee name or {UNASSIGNED!r}).")
        if owner == UNASSIGNED:
            warnings.append(f"{where}: unassigned - confirm an owner.")
        basis = item.get("due_basis")
        if basis not in DUE_BASES:
            errors.append(f"{where}: due_basis must be one of {', '.join(DUE_BASES)}.")
        raw_due = item.get("due_date")
        if raw_due is None:
            if basis in ("explicit", "inferred"):
                errors.append(f"{where}: due_basis is {basis!r} but due_date is null.")
        else:
            due = _parse_date(raw_due)
            if due is None:
                errors.append(f"{where}: due_date must be YYYY-MM-DD or null, got {raw_due!r}.")
            else:
                if basis == "none":
                    errors.append(f"{where}: due_basis 'none' requires due_date null.")
                if meeting_date and due < meeting_date:
                    errors.append(f"{where}: due_date {raw_due} is before the meeting date.")
                if meeting_date and (due - meeting_date).days > 180:
                    warnings.append(f"{where}: due_date is more than 6 months out - check the year.")
        if item.get("priority") not in PRIORITIES:
            errors.append(f"{where}: priority must be one of {', '.join(PRIORITIES)}.")
        if item.get("status", "todo") not in STATUSES:
            errors.append(f"{where}: status must be one of {', '.join(STATUSES)}.")
        deps = item.get("depends_on", [])
        if not isinstance(deps, list):
            errors.append(f"{where}: depends_on must be a list.")
        else:
            for dep in deps:
                if dep == item.get("id"):
                    errors.append(f"{where}: depends on itself.")
                elif dep not in action_ids:
                    errors.append(f"{where}: depends_on references unknown action item {dep!r}.")
        if not isinstance(item.get("labels", []), list):
            errors.append(f"{where}: labels must be a list.")

    # Dependency cycles
    graph = {a.get("id"): [d for d in a.get("depends_on", []) if d in action_ids] for a in actions if isinstance(a, dict)}
    visiting: set[str] = set()
    done: set[str] = set()

    def visit(node: str, path: list[str]) -> None:
        if node in done:
            return
        if node in visiting:
            errors.append(f"Dependency cycle: {' -> '.join(path + [node])}.")
            return
        visiting.add(node)
        for nxt in graph.get(node, []):
            visit(nxt, path + [node])
        visiting.discard(node)
        done.add(node)

    for node in list(graph):
        visit(node, [])

    return errors, warnings


# ---------------------------------------------------------------- export

def _description(item: dict, meeting: dict) -> str:
    parts = [item.get("description", "").strip()]
    parts.append(f'Evidence: "{item.get("source_quote", "").strip()}"')
    parts.append(f'From: {meeting.get("title", "meeting")} ({meeting.get("date", "")})')
    if item.get("depends_on"):
        parts.append("Depends on: " + ", ".join(item["depends_on"]))
    return "\n\n".join(p for p in parts if p)


def export_rows(data: dict, fmt: str) -> tuple[list[str], list[list[str]]]:
    meeting = data["meeting"]
    emails = {p["name"]: p.get("email", "") for p in meeting.get("attendees", [])}
    actions = data.get("action_items", [])

    def assignee(item: dict, prefer_email: bool) -> str:
        owner = item.get("owner", UNASSIGNED)
        if owner == UNASSIGNED:
            return ""
        return (emails.get(owner) or owner) if prefer_email else owner

    if fmt == "jira":
        max_labels = max([len(a.get("labels", [])) for a in actions] + [1])
        header = ["Summary", "Description", "Issue Type", "Priority", "Assignee", "Due Date"] + ["Labels"] * max_labels
        rows = []
        for a in actions:
            labels = [re.sub(r"\s+", "-", label) for label in a.get("labels", [])]
            rows.append(
                [a["title"], _description(a, meeting), "Task", a["priority"].capitalize(), assignee(a, True), a.get("due_date") or ""]
                + labels + [""] * (max_labels - len(labels))
            )
        return header, rows
    if fmt == "asana":
        header = ["Name", "Description", "Assignee", "Due Date", "Priority", "Section"]
        rows = []
        for a in actions:
            due = _parse_date(a.get("due_date"))
            rows.append([a["title"], _description(a, meeting), assignee(a, True), due.strftime("%m/%d/%Y") if due else "",
                         a["priority"].capitalize(), f'{a["priority"].capitalize()} priority'])
        return header, rows
    if fmt == "notion":
        header = ["Name", "Assignee", "Due", "Priority", "Status", "Depends on", "Source"]
        status = {"todo": "Not started", "in_progress": "In progress", "done": "Done"}
        rows = [[a["title"], assignee(a, False), a.get("due_date") or "", a["priority"].capitalize(), status[a.get("status", "todo")],
                 ", ".join(a.get("depends_on", [])), a.get("source_quote", "")] for a in actions]
        return header, rows
    if fmt == "generic":
        header = ["id", "title", "owner", "owner_email", "due_date", "due_basis", "priority", "status", "depends_on", "labels", "description", "source_quote"]
        rows = [[a["id"], a["title"], a.get("owner", ""), emails.get(a.get("owner", ""), ""), a.get("due_date") or "", a.get("due_basis", ""),
                 a["priority"], a.get("status", "todo"), " ".join(a.get("depends_on", [])), " ".join(a.get("labels", [])),
                 a.get("description", ""), a.get("source_quote", "")] for a in actions]
        return header, rows
    raise ValueError(f"Unknown format {fmt!r}")


def to_csv(header: list[str], rows: list[list[str]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return buffer.getvalue()


def _load(path: str) -> object:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.exit(f"error: {path} not found")
    except json.JSONDecodeError as exc:
        print(f"error: {path} is not valid JSON: {exc}", file=sys.stderr)
        sys.exit(1)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    v = sub.add_parser("validate", help="check tasks.json against the schema")
    v.add_argument("file")
    v.add_argument("--transcript", help="source transcript/notes; verifies every source_quote appears in it")
    e = sub.add_parser("export", help="write tracker CSV (validates first)")
    e.add_argument("file")
    e.add_argument("--format", required=True, choices=["jira", "asana", "notion", "generic"])
    e.add_argument("-o", "--output", help="output CSV path (default: stdout)")
    args = parser.parse_args(argv)

    data = _load(args.file)
    transcript = None
    if getattr(args, "transcript", None):
        transcript = Path(args.transcript).read_text(encoding="utf-8")
    errors, warnings = validate(data, transcript)

    if args.command == "validate":
        for w in warnings:
            print(f"warning: {w}")
        for err in errors:
            print(f"error: {err}")
        n_actions = len(data.get("action_items", [])) if isinstance(data, dict) else 0
        status = "FAILED" if errors else "OK"
        quotes = " (quotes checked against transcript)" if transcript else ""
        print(f"{status}: {n_actions} action items, {len(errors)} error(s), {len(warnings)} warning(s){quotes}")
        return 1 if errors else 0

    if errors:
        for err in errors:
            print(f"error: {err}", file=sys.stderr)
        print("Refusing to export invalid data - run `validate` and fix the errors first.", file=sys.stderr)
        return 1
    header, rows = export_rows(data, args.format)  # type: ignore[arg-type]
    text = to_csv(header, rows)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Wrote {len(rows)} {args.format} rows to {args.output}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
