#!/usr/bin/env python3
"""Deterministic brand-voice checks for a draft.

Usage:
  python check_draft.py --guide voice-guide.md --channel linkedin draft.md [--json]

Reads the ```voice-rules block from the voice guide (avoid list, max sentence
length, max exclamations/emoji/hashtags, min reading ease) and checks the draft,
plus the length limit for the channel. Exit 0 = pass, 1 = a hard rule failed,
2 = usage error. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# (unit, max) per channel; see references/channel-formats.md
CHANNEL_LIMITS = {
    "linkedin": ("words", 250),
    "x": ("chars", 280),
    "instagram": ("words", 200),
    "facebook": ("words", 150),
    "email": ("words", 350),
    "newsletter": ("words", 700),
    "product": ("words", 200),
    "ad": ("chars", None),
    "generic": ("words", None),
}
EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿⬀-⯿️]")
HASHTAG = re.compile(r"(?<![\w&])#[A-Za-z0-9_]+")
WORD = re.compile(r"[A-Za-z0-9À-ɏ]+(?:['’][A-Za-z]+)*")


def parse_rules(guide_text: str) -> dict:
    match = re.search(r"```voice-rules\s*\n(.*?)```", guide_text, re.S)
    if not match:
        raise ValueError("No ```voice-rules block found in the voice guide (see assets/voice-guide-template.md).")
    rules: dict = {}
    for line in match.group(1).splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if "{{" in value:
            raise ValueError(f"voice-rules '{key}' still contains a template placeholder.")
        if key == "avoid":
            rules[key] = [w.strip() for w in value.split(",") if w.strip()]
        elif key in {"max_sentence_words", "max_exclamations", "max_emoji", "max_hashtags", "min_reading_ease"}:
            rules[key] = float(value) if key == "min_reading_ease" else int(value)
        else:
            raise ValueError(f"Unknown voice-rules key '{key}'.")
    return rules


def strip_markdown(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"^\s{0,3}#{1,6}\s+", "", text, flags=re.M)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.M)
    return text.replace("**", "").replace("__", "").replace("`", "")


def syllables(word: str) -> int:
    w = word.lower().strip("'’")
    if len(w) <= 3:
        return 1
    w = re.sub(r"(?:[^laeiouy]es|[^laeiouy]ed|[^laeiouy]e)$", "", w)
    w = re.sub(r"^y", "", w)
    return max(1, len(re.findall(r"[aeiouy]{1,2}", w)))


def sentences_of(text: str) -> list[str]:
    chunks: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or HASHTAG.fullmatch(line.split()[0]) and all(HASHTAG.fullmatch(t) for t in line.split()):
            continue
        chunks.extend(s.strip() for s in re.split(r"(?<=[.!?])\s+", line) if s.strip())
    return chunks


def check(draft: str, rules: dict, channel: str) -> dict:
    lines = draft.splitlines()
    header: dict[str, str] = {}
    body_lines = []
    for line in lines:
        m = re.match(r"^(Subject|Preview|Headline|Body):\s*(.*)$", line.strip(), re.I)
        if m and m.group(1).lower() in ("subject", "preview"):
            header[m.group(1).lower()] = m.group(2).strip()
        else:
            body_lines.append(line)
    body = strip_markdown("\n".join(body_lines)).strip()
    words = WORD.findall(body)
    sentences = sentences_of(body)
    failures: list[str] = []
    warnings: list[str] = []
    metrics: dict = {"words": len(words), "characters": len(body), "sentences": len(sentences)}

    # Banned vocabulary (whole words / phrases, case-insensitive), searched in the full draft incl. subject
    hits = []
    for term in rules.get("avoid", []):
        pattern = re.compile(r"(?<![\w-])" + re.escape(term).replace(r"\ ", r"\s+") + r"(?![\w-])", re.I)
        for i, line in enumerate(lines, 1):
            for _ in pattern.finditer(line):
                hits.append({"term": term, "line": i})
    metrics["banned_terms"] = hits
    if hits:
        failures.append("Banned terms: " + ", ".join(f"'{h['term']}' (line {h['line']})" for h in hits))

    max_words = rules.get("max_sentence_words")
    lengths = [(len(WORD.findall(s)), s) for s in sentences]
    metrics["longest_sentence_words"] = max((n for n, _ in lengths), default=0)
    if max_words:
        for n, s in lengths:
            if n > max_words:
                failures.append(f"Sentence has {n} words (max {max_words}): \"{s[:70]}...\"")

    counts = {
        "exclamations": draft.count("!"),
        "emoji": len(EMOJI.findall(draft)),
        "hashtags": len(HASHTAG.findall(draft)),
    }
    metrics.update(counts)
    for key, rule in (("exclamations", "max_exclamations"), ("emoji", "max_emoji"), ("hashtags", "max_hashtags")):
        if rule in rules and counts[key] > rules[rule]:
            failures.append(f"{counts[key]} {key} (max {rules[rule]}).")

    if words and sentences:
        syl = sum(syllables(w) for w in words)
        ease = 206.835 - 1.015 * (len(words) / len(sentences)) - 84.6 * (syl / len(words))
        metrics["reading_ease"] = round(ease, 1)
        if "min_reading_ease" in rules and ease < rules["min_reading_ease"]:
            warnings.append(f"Reading ease {ease:.0f} is below the target {rules['min_reading_ease']:.0f} - shorten sentences or use simpler words.")

    unit, limit = CHANNEL_LIMITS[channel]
    if channel == "ad":
        for line in lines:
            m = re.match(r"^(Headline|Body):\s*(.*)$", line.strip(), re.I)
            if m:
                cap = 40 if m.group(1).lower() == "headline" else 125
                if len(m.group(2)) > cap:
                    failures.append(f"{m.group(1)} is {len(m.group(2))} characters (max {cap}).")
    elif limit is not None:
        size = len(words) if unit == "words" else len(draft.strip())
        metrics["limit"] = f"{size}/{limit} {unit}"
        if size > limit:
            failures.append(f"Too long for {channel}: {size} {unit} (max {limit}).")

    if channel in ("email", "newsletter"):
        subject = header.get("subject")
        if not subject:
            failures.append("Email needs a 'Subject:' line at the top.")
        elif len(subject) > 50:
            warnings.append(f"Subject is {len(subject)} characters; under 50 avoids truncation on mobile.")
        if "preview" not in header:
            warnings.append("No 'Preview:' line - inbox will show the first body text instead.")
        elif len(header["preview"]) > 90:
            warnings.append(f"Preview is {len(header['preview'])} characters (aim for under 90).")

    return {"channel": channel, "passed": not failures, "failures": failures, "warnings": warnings, "metrics": metrics}


def format_report(name: str, result: dict, rules: dict) -> str:
    m = result["metrics"]
    parts = [f"words {m['words']}"]
    if "limit" in m:
        parts[0] = f"length {m['limit']}"
    if "max_sentence_words" in rules:
        parts.append(f"longest sentence {m['longest_sentence_words']}/{rules['max_sentence_words']}")
    if "reading_ease" in m:
        parts.append(f"reading ease {m['reading_ease']:.0f}")
    for key, rule in (("emoji", "max_emoji"), ("exclamations", "max_exclamations"), ("hashtags", "max_hashtags")):
        if rule in rules:
            parts.append(f"{key} {m[key]}/{rules[rule]}")
    out = [f"{name} [{result['channel']}]: {'PASS' if result['passed'] else 'FAIL'} ({', '.join(parts)})"]
    out += [f"  FAIL  {f}" for f in result["failures"]]
    out += [f"  WARN  {w}" for w in result["warnings"]]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("drafts", nargs="+", help="draft file(s) (Markdown or plain text)")
    parser.add_argument("--guide", required=True, help="voice guide containing a ```voice-rules block")
    parser.add_argument("--channel", default="generic", choices=sorted(CHANNEL_LIMITS))
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    args = parser.parse_args(argv)
    try:
        rules = parse_rules(Path(args.guide).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    results = {}
    for path in args.drafts:
        try:
            results[path] = check(Path(path).read_text(encoding="utf-8"), rules, args.channel)
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print("\n".join(format_report(p, r, rules) for p, r in results.items()))
    return 0 if all(r["passed"] for r in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
